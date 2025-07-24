"""
Simple FLUX handler for RunPod with ComfyUI
Supports basic text-to-image generation with FLUX
"""

import runpod
import json
import requests
import time
import os
import boto3
import base64
from typing import Dict, Any
import subprocess
import threading

# Start ComfyUI server
def start_comfyui_server():
    cmd = ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
    subprocess.Popen(cmd, cwd="/ComfyUI")
    
    # Wait for server to start
    for i in range(30):
        try:
            response = requests.get("http://localhost:8188/system_stats")
            if response.status_code == 200:
                print("ComfyUI server started successfully")
                return
        except:
            pass
        time.sleep(1)
    raise Exception("Failed to start ComfyUI server")

# Start server on container start
threading.Thread(target=start_comfyui_server, daemon=True).start()
time.sleep(10)

# R2 client setup (optional)
s3_client = None
if os.environ.get('R2_ENDPOINT'):
    s3_client = boto3.client(
        's3',
        endpoint_url=os.environ.get('R2_ENDPOINT'),
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY')
    )

class FluxHandler:
    def __init__(self):
        self.server_url = "http://localhost:8188"
        self.workflow_path = "/workflows/flux_simple.json"
        
    def load_workflow(self) -> Dict:
        """Load the FLUX workflow template"""
        with open(self.workflow_path, 'r') as f:
            return json.load(f)
    
    def update_prompt(self, workflow: Dict, prompt: str, width: int = 1024, height: int = 1024) -> Dict:
        """Update workflow with user prompt and dimensions"""
        # Find and update prompt node
        for node_id, node in workflow.items():
            if node.get("class_type") == "CLIPTextEncodeFlux":
                node["inputs"]["text"] = prompt
                node["inputs"]["guidance"] = 3.5  # FLUX works best with lower guidance
            
            # Update dimensions
            elif node.get("class_type") == "EmptyLatentImage":
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height
        
        return workflow
    
    def queue_prompt(self, workflow: Dict) -> str:
        """Queue workflow and return prompt ID"""
        p = {"prompt": workflow}
        response = requests.post(f"{self.server_url}/prompt", json=p)
        return response.json()['prompt_id']
    
    def wait_for_image(self, prompt_id: str, timeout: int = 120) -> bytes:
        """Wait for and retrieve generated image"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check history
            response = requests.get(f"{self.server_url}/history/{prompt_id}")
            history = response.json()
            
            if prompt_id in history:
                outputs = history[prompt_id].get('outputs', {})
                
                # Find image in outputs
                for node_id, node_output in outputs.items():
                    if 'images' in node_output and len(node_output['images']) > 0:
                        image = node_output['images'][0]
                        
                        # Fetch image data
                        image_data = requests.get(
                            f"{self.server_url}/view",
                            params={
                                'filename': image['filename'],
                                'subfolder': image.get('subfolder', ''),
                                'type': image.get('type', 'output')
                            }
                        ).content
                        
                        return image_data
            
            time.sleep(1)
        
        raise TimeoutError("Image generation timed out")
    
    def upload_to_r2(self, image_data: bytes, job_id: str) -> str:
        """Upload to R2 and return URL"""
        if not s3_client:
            # No R2 configured, return base64
            return base64.b64encode(image_data).decode('utf-8')
        
        key = f"flux/{job_id}/image.png"
        s3_client.put_object(
            Bucket=os.environ.get('R2_BUCKET'),
            Key=key,
            Body=image_data,
            ContentType='image/png'
        )
        
        base_url = os.environ.get('R2_PUBLIC_URL', '').rstrip('/')
        return f"{base_url}/{key}"

handler = FluxHandler()

def runpod_handler(job):
    """
    Simple FLUX handler
    Input format:
    {
        "input": {
            "prompt": "a beautiful landscape",
            "width": 1024,
            "height": 1024
        }
    }
    """
    try:
        job_input = job['input']
        prompt = job_input.get('prompt', 'a beautiful landscape')
        width = job_input.get('width', 1024)
        height = job_input.get('height', 1024)
        
        print(f"Generating FLUX image: {prompt}")
        
        # Load and update workflow
        workflow = handler.load_workflow()
        workflow = handler.update_prompt(workflow, prompt, width, height)
        
        # Queue generation
        prompt_id = handler.queue_prompt(workflow)
        print(f"Queued with ID: {prompt_id}")
        
        # Wait for result
        image_data = handler.wait_for_image(prompt_id)
        
        # Upload or return
        if s3_client:
            url = handler.upload_to_r2(image_data, job.get('id', 'test'))
            return {
                "status": "success",
                "image_url": url,
                "model": "flux-dev"
            }
        else:
            # Return base64 (watch size!)
            return {
                "status": "success",
                "image": base64.b64encode(image_data).decode('utf-8'),
                "model": "flux-dev"
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# Start RunPod handler
runpod.serverless.start({"handler": runpod_handler})