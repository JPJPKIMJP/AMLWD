"""
Simple FLUX handler for RunPod with ComfyUI
Supports basic text-to-image generation with FLUX
"""

import runpod
from runpod.serverless.modules.rp_logger import RunPodLogger
import json
import requests
import time
import os
import boto3
import base64
from typing import Dict, Any
import subprocess
import threading

# Initialize RunPod logger
logger = RunPodLogger()

# Start ComfyUI server
def start_comfyui_server():
    logger.info("Starting ComfyUI server...")
    cmd = ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
    subprocess.Popen(cmd, cwd="/ComfyUI")
    
    # Wait for server to start
    for i in range(30):
        try:
            response = requests.get("http://localhost:8188/system_stats")
            if response.status_code == 200:
                logger.info("ComfyUI server started successfully")
                return
        except Exception as e:
            if i % 5 == 0:
                logger.debug(f"Waiting for ComfyUI... attempt {i}/30")
        time.sleep(1)
    raise Exception("Failed to start ComfyUI server")

# Start server on container start
logger.info("Initializing FLUX handler...")
threading.Thread(target=start_comfyui_server, daemon=True).start()
time.sleep(10)

# R2 client setup (optional)
s3_client = None
if os.environ.get('R2_ENDPOINT'):
    logger.info("Setting up R2 client...")
    s3_client = boto3.client(
        's3',
        endpoint_url=os.environ.get('R2_ENDPOINT'),
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY')
    )
    logger.info(f"R2 client configured for bucket: {os.environ.get('R2_BUCKET')}")
else:
    logger.warning("R2 not configured - will return base64")

class FluxHandler:
    def __init__(self):
        self.server_url = "http://localhost:8188"
        self.workflow_path = "/workflows/flux_simple.json"
        self.check_models()
        
    def load_workflow(self) -> Dict:
        """Load the FLUX workflow template"""
        # Check if we have checkpoint models
        checkpoint_path = "/ComfyUI/models/checkpoints"
        if os.path.exists(checkpoint_path) and os.listdir(checkpoint_path):
            logger.info("Using checkpoint workflow")
            workflow_file = "/workflows/flux_checkpoint.json"
        else:
            logger.info("Using default FLUX workflow")
            workflow_file = self.workflow_path
            
        with open(workflow_file, 'r') as f:
            return json.load(f)
    
    def update_prompt(self, workflow: Dict, prompt: str, width: int = 1024, height: int = 1024) -> Dict:
        """Update workflow with user prompt and dimensions"""
        # Find and update prompt node
        for node_id, node in workflow.items():
            # Handle both FLUX and standard CLIP encoding
            if node.get("class_type") in ["CLIPTextEncodeFlux", "CLIPTextEncode"]:
                if "text" in node["inputs"]:
                    # Only update if it's the positive prompt (not negative)
                    if node.get("_meta", {}).get("title", "").lower().find("negative") == -1:
                        node["inputs"]["text"] = prompt
                        if "guidance" in node["inputs"]:
                            node["inputs"]["guidance"] = 3.5
            
            # Update dimensions
            elif node.get("class_type") == "EmptyLatentImage":
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height
        
        return workflow
    
    def check_models(self):
        """Check available models"""
        import os
        
        # Check different possible mount points
        mount_points = ["/workspace", "/runpod-volume", "/"]
        for mount in mount_points:
            if os.path.exists(mount):
                logger.info(f"Mount point {mount} exists. Contents: {os.listdir(mount)[:10]}")
                
        model_dirs = [
            "/ComfyUI/models/vae",
            "/ComfyUI/models/unet", 
            "/ComfyUI/models/checkpoints",
            "/ComfyUI/models/clip",
            "/workspace/ComfyUI/models/vae",
            "/workspace/ComfyUI/models/unet",
            "/workspace/ComfyUI/models/checkpoints",
            "/workspace/ComfyUI/models/clip",
            "/runpod-volume/ComfyUI/models/vae",
            "/runpod-volume/ComfyUI/models/unet",
            "/runpod-volume/ComfyUI/models/checkpoints",
            "/runpod-volume/ComfyUI/models/clip"
        ]
        
        for dir_path in model_dirs:
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                if files:
                    logger.info(f"Models in {dir_path}: {files[:5]}...")  # Show first 5
            else:
                logger.debug(f"Directory not found: {dir_path}")
    
    def queue_prompt(self, workflow: Dict) -> str:
        """Queue workflow and return prompt ID"""
        p = {"prompt": workflow}
        logger.debug(f"Queueing prompt to {self.server_url}/prompt")
        try:
            response = requests.post(f"{self.server_url}/prompt", json=p)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Queue response: {result}")
            if 'prompt_id' not in result:
                logger.error(f"No prompt_id in response: {result}")
                raise ValueError(f"Invalid response from ComfyUI: {result}")
            return result['prompt_id']
        except Exception as e:
            logger.error(f"Failed to queue prompt: {str(e)}")
            raise
    
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
        
        logger.info(f"Generating FLUX image: {prompt}")
        logger.info(f"Dimensions: {width}x{height}")
        
        # Load and update workflow
        workflow = handler.load_workflow()
        workflow = handler.update_prompt(workflow, prompt, width, height)
        
        # Queue generation
        prompt_id = handler.queue_prompt(workflow)
        logger.info(f"Queued with ID: {prompt_id}")
        
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
        logger.error(f"Handler error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": str(e)
        }

# Start RunPod handler
runpod.serverless.start({"handler": runpod_handler})