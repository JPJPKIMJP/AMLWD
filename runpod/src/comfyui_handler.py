"""
ComfyUI RunPod Handler with Full Workflow Flexibility
Supports both pre-defined templates and custom workflows
"""

import runpod
import json
import requests
import time
import os
import boto3
from typing import Dict, Any, List, Optional
import base64
from io import BytesIO
from PIL import Image
import subprocess
import threading

# Start ComfyUI server in background
def start_comfyui_server():
    cmd = ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--gpu-only"]
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

# Initialize ComfyUI on container start
threading.Thread(target=start_comfyui_server, daemon=True).start()
time.sleep(10)  # Give it time to start

# S3/R2 client for image storage (optional)
s3_client = None
if os.environ.get('R2_ENDPOINT'):
    s3_client = boto3.client(
        's3',
        endpoint_url=os.environ.get('R2_ENDPOINT'),
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY')
    )

class ComfyUIHandler:
    def __init__(self):
        self.server_url = "http://localhost:8188"
        self.workflow_dir = "/workflows"
        
    def load_workflow_template(self, template_name: str) -> Dict:
        """Load a pre-defined workflow template"""
        template_path = os.path.join(self.workflow_dir, f"{template_name}.json")
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return json.load(f)
        else:
            raise ValueError(f"Workflow template '{template_name}' not found")
    
    def update_workflow_inputs(self, workflow: Dict, inputs: Dict) -> Dict:
        """Update workflow with user inputs"""
        # Find and update prompt nodes
        for node_id, node in workflow.items():
            if node.get("class_type") == "CLIPTextEncode":
                if node.get("_meta", {}).get("title") == "Positive Prompt":
                    node["inputs"]["text"] = inputs.get("prompt", "")
                elif node.get("_meta", {}).get("title") == "Negative Prompt":
                    node["inputs"]["text"] = inputs.get("negative_prompt", "")
            
            # Update model selection
            elif node.get("class_type") == "CheckpointLoaderSimple":
                if "model" in inputs:
                    node["inputs"]["ckpt_name"] = inputs["model"]
            
            # Update LoRA nodes
            elif node.get("class_type") in ["LoraLoader", "LoraLoaderModelOnly"]:
                if "lora" in inputs:
                    node["inputs"]["lora_name"] = inputs["lora"]["name"]
                    node["inputs"]["strength_model"] = inputs["lora"].get("strength", 0.8)
                    node["inputs"]["strength_clip"] = inputs["lora"].get("strength", 0.8)
            
            # Update sampler settings
            elif node.get("class_type") == "KSampler":
                if "seed" in inputs:
                    node["inputs"]["seed"] = inputs["seed"]
                if "steps" in inputs:
                    node["inputs"]["steps"] = inputs["steps"]
                if "cfg" in inputs:
                    node["inputs"]["cfg"] = inputs["cfg"]
                if "sampler_name" in inputs:
                    node["inputs"]["sampler_name"] = inputs["sampler_name"]
                if "scheduler" in inputs:
                    node["inputs"]["scheduler"] = inputs["scheduler"]
            
            # Update image dimensions
            elif node.get("class_type") == "EmptyLatentImage":
                if "width" in inputs:
                    node["inputs"]["width"] = inputs["width"]
                if "height" in inputs:
                    node["inputs"]["height"] = inputs["height"]
                if "batch_size" in inputs:
                    node["inputs"]["batch_size"] = inputs["batch_size"]
        
        return workflow
    
    def queue_prompt(self, workflow: Dict) -> str:
        """Queue a workflow and return the prompt ID"""
        p = {"prompt": workflow}
        response = requests.post(f"{self.server_url}/prompt", json=p)
        return response.json()['prompt_id']
    
    def get_history(self, prompt_id: str) -> Optional[Dict]:
        """Get the history for a prompt ID"""
        response = requests.get(f"{self.server_url}/history/{prompt_id}")
        return response.json()
    
    def get_images(self, prompt_id: str) -> List[bytes]:
        """Wait for and retrieve generated images"""
        # Poll for completion
        for _ in range(300):  # 5 minute timeout
            history = self.get_history(prompt_id)
            if history and prompt_id in history:
                outputs = history[prompt_id].get('outputs', {})
                images = []
                
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        for image in node_output['images']:
                            image_data = requests.get(
                                f"{self.server_url}/view",
                                params={
                                    'filename': image['filename'],
                                    'subfolder': image['subfolder'],
                                    'type': image['type']
                                }
                            ).content
                            images.append(image_data)
                
                return images
            time.sleep(1)
        
        raise TimeoutError("Image generation timed out")
    
    def upload_to_storage(self, image_data: bytes, job_id: str, index: int) -> str:
        """Upload image to R2/S3 and return URL"""
        if not s3_client:
            # If no S3, return base64 (fallback)
            return base64.b64encode(image_data).decode('utf-8')
        
        key = f"comfyui/{job_id}/image_{index}.png"
        s3_client.put_object(
            Bucket=os.environ.get('R2_BUCKET'),
            Key=key,
            Body=image_data,
            ContentType='image/png'
        )
        
        base_url = os.environ.get('R2_PUBLIC_URL', '').rstrip('/')
        return f"{base_url}/{key}"

def download_lora_if_needed(lora_name: str) -> bool:
    """Download LoRA file from Firebase Storage if not present locally"""
    lora_dir = "/ComfyUI/models/loras"
    lora_path = os.path.join(lora_dir, lora_name)
    
    # Check if LoRA already exists
    if os.path.exists(lora_path):
        print(f"LoRA {lora_name} already exists locally")
        return True
    
    # Ensure LoRA directory exists
    os.makedirs(lora_dir, exist_ok=True)
    
    # Firebase Storage URLs for known LoRAs
    firebase_urls = {
        "mix4.safetensors": "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753591512468_mix4.safetensors?alt=media&token=d2c720b3-4aef-4ac4-8651-4a93b936fbeb",
        "shiyuanlimei.safetensors": "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2Fshiyuanlimei.safetensors?alt=media"
    }
    
    if lora_name in firebase_urls:
        try:
            print(f"Downloading LoRA {lora_name} from Firebase Storage...")
            response = requests.get(firebase_urls[lora_name], stream=True)
            response.raise_for_status()
            
            with open(lora_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Successfully downloaded LoRA {lora_name}")
            return True
        except Exception as e:
            print(f"Failed to download LoRA {lora_name}: {e}")
            return False
    else:
        print(f"Unknown LoRA {lora_name}, no download URL available")
        return False

handler_instance = ComfyUIHandler()

def handler(job):
    """
    RunPod handler that supports multiple workflow modes
    
    Input formats:
    1. Template mode:
    {
        "workflow_type": "sd15_basic",
        "prompt": "a cat",
        "model": "sd_v1-5.safetensors",
        "lora": {"name": "style.safetensors", "strength": 0.8}
    }
    
    2. Custom workflow mode:
    {
        "custom_workflow": { ...complete ComfyUI workflow... },
        "override_inputs": {
            "prompt": "override the prompt in workflow"
        }
    }
    
    3. Hybrid mode:
    {
        "workflow_type": "sd15_lora",
        "modifications": {
            "add_controlnet": true,
            "controlnet_image": "base64..."
        },
        "inputs": { ...standard inputs... }
    }
    """
    try:
        job_input = job['input']
        job_id = job.get('id', 'unknown')
        
        # Determine workflow source
        if 'custom_workflow' in job_input:
            # User provided complete workflow
            workflow = job_input['custom_workflow']
            if 'override_inputs' in job_input:
                workflow = handler_instance.update_workflow_inputs(
                    workflow, 
                    job_input['override_inputs']
                )
        else:
            # Determine workflow type based on inputs
            inputs = job_input.get('inputs', job_input)
            
            # Check if LoRA is requested
            if 'lora' in inputs and inputs['lora'].get('name') != 'none':
                lora_name = inputs['lora']['name']
                print(f"LoRA requested: {lora_name}")
                
                # Download LoRA if needed
                if download_lora_if_needed(lora_name):
                    workflow_type = 'flux_with_lora'
                    print(f"Using LoRA workflow: {workflow_type}")
                else:
                    print(f"LoRA download failed, falling back to basic workflow")
                    workflow_type = job_input.get('workflow_type', 'flux_simple')
            else:
                workflow_type = job_input.get('workflow_type', 'flux_simple')
                print(f"Using basic workflow: {workflow_type}")
            
            workflow = handler_instance.load_workflow_template(workflow_type)
            
            # Apply inputs
            if 'inputs' in job_input:
                workflow = handler_instance.update_workflow_inputs(
                    workflow,
                    job_input['inputs']
                )
            else:
                # For backward compatibility
                workflow = handler_instance.update_workflow_inputs(
                    workflow,
                    job_input
                )
        
        # Queue the prompt
        prompt_id = handler_instance.queue_prompt(workflow)
        print(f"Queued prompt: {prompt_id}")
        
        # Wait for and get images
        images = handler_instance.get_images(prompt_id)
        
        # Process results
        results = []
        for i, image_data in enumerate(images):
            if s3_client:
                # Upload to storage and return URL
                url = handler_instance.upload_to_storage(image_data, job_id, i)
                results.append({"url": url})
            else:
                # Return base64 (watch the size limit!)
                b64 = base64.b64encode(image_data).decode('utf-8')
                results.append({"base64": b64})
        
        return {
            "status": "success",
            "images": results,
            "prompt_id": prompt_id,
            "workflow_type": job_input.get('workflow_type', 'custom')
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }

# Start RunPod serverless worker
runpod.serverless.start({"handler": handler})