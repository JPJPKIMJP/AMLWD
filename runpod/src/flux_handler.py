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
        self.workflow_path = "/workflows/flux_actual.json"
        self.check_models()
        
    def load_workflow(self, is_img2img: bool = False, lora_name: str = None) -> Dict:
        """Load the FLUX workflow template"""
        # Try multiple possible paths for workflows
        workflow_paths = [
            "/workflows/",
            "/src/workflows/",
            "/app/workflows/",
            "./workflows/",
            "workflows/"
        ]
        
        # Determine which workflow to use
        if is_img2img:
            logger.info("Using image-to-image workflow")
            workflow_filename = "flux_img2img.json"
        elif lora_name:
            logger.info(f"Using LoRA workflow with: {lora_name}")
            workflow_filename = "flux_with_lora.json"
        else:
            logger.info("Using text-to-image workflow")
            workflow_filename = "flux_actual.json"
            
        # Find the workflow file
        workflow_file = None
        for path in workflow_paths:
            test_path = os.path.join(path, workflow_filename)
            if os.path.exists(test_path):
                workflow_file = test_path
                logger.info(f"Found workflow at: {test_path}")
                break
                
        if not workflow_file:
            # If no workflow found, try to construct path based on current file location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            workflow_file = os.path.join(current_dir, "workflows", workflow_filename)
            if not os.path.exists(workflow_file):
                logger.error(f"Could not find workflow file: {workflow_filename}")
                raise FileNotFoundError(f"Workflow file not found: {workflow_filename}")
            
        with open(workflow_file, 'r') as f:
            return json.load(f)
    
    def update_prompt(self, workflow: Dict, prompt: str, width: int = 1024, height: int = 1024, image_data: bytes = None, lora_name: str = None, lora_strength: float = 1.0) -> Dict:
        """Update workflow with user prompt and dimensions"""
        import random
        
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
            
            # Update seed with random value if it's 0
            elif node.get("class_type") == "KSampler":
                if node["inputs"].get("seed", 0) == 0:
                    node["inputs"]["seed"] = random.randint(1, 2**32 - 1)
        
        # Handle image input for image-to-image
        if image_data:
            # Save image temporarily
            import uuid
            temp_image = f"/tmp/input_{uuid.uuid4()}.png"
            with open(temp_image, 'wb') as f:
                f.write(image_data)
            
            # Update LoadImage node if it exists
            for node_id, node in workflow.items():
                if node.get("class_type") == "LoadImage":
                    node["inputs"]["image"] = temp_image
                    
                # Switch KSampler to use VAEEncode instead of EmptyLatentImage
                elif node.get("class_type") == "KSampler":
                    # Find VAEEncode node
                    vae_encode_id = None
                    for nid, n in workflow.items():
                        if n.get("class_type") == "VAEEncode":
                            vae_encode_id = nid
                            break
                    if vae_encode_id:
                        node["inputs"]["latent_image"] = [vae_encode_id, 0]
        
        # Update LoRA if specified
        if lora_name:
            # Ensure lora_name has the .safetensors extension
            if not lora_name.endswith('.safetensors'):
                lora_filename = f"{lora_name}.safetensors"
            else:
                lora_filename = lora_name
                
            # Check various possible locations for the LoRA
            lora_paths = [
                f"/ComfyUI/models/loras/{lora_filename}",
                f"/workspace/ComfyUI/models/loras/{lora_filename}",
                f"/runpod-volume/ComfyUI/models/loras/{lora_filename}"
            ]
            
            lora_exists = False
            for path in lora_paths:
                if os.path.exists(path):
                    lora_exists = True
                    logger.info(f"Found LoRA at: {path}")
                    break
                    
            if not lora_exists:
                logger.info(f"LoRA {lora_filename} not found locally, checking known LoRAs...")
                
                # Known LoRAs mapping
                known_loras = {
                    "shiyuanlimei_v1.0": "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753410944552_shiyuanlimei_v1.0.safetensors?alt=media&token=c1abf95f-1b20-422b-90fb-66347fe66367",
                    "mix4": "PLACEHOLDER_URL_FOR_MIX4"  # Need to get the actual URL
                }
                
                if lora_name in known_loras:
                    logger.info(f"Downloading {lora_name}...")
                    try:
                        import urllib.request
                        # Try to download to the first writable location
                        for path in lora_paths:
                            try:
                                os.makedirs(os.path.dirname(path), exist_ok=True)
                                urllib.request.urlretrieve(known_loras[lora_name], path)
                                logger.info(f"Successfully downloaded {lora_name} to {path}")
                                lora_exists = True
                                break
                            except Exception as e:
                                logger.warning(f"Could not write to {path}: {e}")
                    except Exception as e:
                        logger.error(f"Failed to download LoRA: {e}")
            
            # Update LoRA nodes with the filename (ComfyUI expects filename with extension)
            lora_updated = False
            for node_id, node in workflow.items():
                if node.get("class_type") in ["LoraLoader", "LoraLoaderModelOnly"]:
                    node["inputs"]["lora_name"] = lora_filename
                    node["inputs"]["strength_model"] = lora_strength
                    logger.info(f"Updated LoRA node {node_id}: {lora_filename} with strength {lora_strength}")
                    lora_updated = True
                    
            if not lora_updated:
                logger.warning(f"No LoRA nodes found in workflow to update!")
        
        return workflow
    
    def check_models(self):
        """Check available models"""
        import os
        
        # Check different possible mount points
        mount_points = ["/workspace", "/runpod-volume", "/"]
        for mount in mount_points:
            if os.path.exists(mount):
                logger.info(f"Mount point {mount} exists. Contents: {os.listdir(mount)[:10]}")
                
        # Specifically check for FLUX model
        flux_model = "flux1-dev-kontext_fp8_scaled.safetensors"
        flux_locations = [
            f"/ComfyUI/models/diffusion_models/{flux_model}",
            f"/ComfyUI/models/checkpoints/{flux_model}",
            f"/ComfyUI/models/unet/{flux_model}",
            f"/runpod-volume/ComfyUI/models/diffusion_models/{flux_model}",
            f"/runpod-volume/ComfyUI/models/checkpoints/{flux_model}",
            f"/workspace/ComfyUI/models/diffusion_models/{flux_model}"
        ]
        
        logger.info(f"Searching for FLUX model: {flux_model}")
        for path in flux_locations:
            if os.path.exists(path):
                logger.info(f"✓ FLUX MODEL FOUND at: {path}")
                logger.info(f"  File size: {os.path.getsize(path) / (1024**3):.2f} GB")
            else:
                logger.debug(f"✗ Not at: {path}")
                
        # Check diffusion_models directory specifically
        logger.info("Checking diffusion_models directories:")
        diffusion_dirs = [
            "/ComfyUI/models/diffusion_models",
            "/runpod-volume/ComfyUI/models/diffusion_models",
            "/workspace/ComfyUI/models/diffusion_models"
        ]
        
        for dir_path in diffusion_dirs:
            if os.path.exists(dir_path):
                logger.info(f"Directory {dir_path} exists")
                files = os.listdir(dir_path)
                logger.info(f"  Contents ({len(files)} files): {files[:3]}...")
                # Check if it's a symlink
                if os.path.islink(dir_path):
                    logger.info(f"  -> Symlink to: {os.readlink(dir_path)}")
            else:
                logger.info(f"Directory {dir_path} does NOT exist")
                
        model_dirs = [
            "/ComfyUI/models/vae",
            "/ComfyUI/models/unet", 
            "/ComfyUI/models/checkpoints",
            "/ComfyUI/models/clip",
            "/ComfyUI/models/diffusion_models",
            "/workspace/ComfyUI/models/vae",
            "/workspace/ComfyUI/models/unet",
            "/workspace/ComfyUI/models/checkpoints",
            "/workspace/ComfyUI/models/clip",
            "/workspace/ComfyUI/models/diffusion_models",
            "/runpod-volume/ComfyUI/models/vae",
            "/runpod-volume/ComfyUI/models/unet",
            "/runpod-volume/ComfyUI/models/checkpoints",
            "/runpod-volume/ComfyUI/models/clip",
            "/runpod-volume/ComfyUI/models/diffusion_models"
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
    
    def wait_for_image(self, prompt_id: str, timeout: int = 300) -> bytes:
        """Wait for and retrieve generated image"""
        start_time = time.time()
        
        last_log_time = start_time
        while time.time() - start_time < timeout:
            # Log progress every 30 seconds
            if time.time() - last_log_time > 30:
                elapsed = int(time.time() - start_time)
                logger.info(f"Still waiting for image... {elapsed}s elapsed")
                last_log_time = time.time()
                
            # Check queue status first
            queue_response = requests.get(f"{self.server_url}/queue")
            queue_data = queue_response.json()
            
            # Log if our prompt is still in queue
            if queue_data.get('queue_running'):
                for item in queue_data['queue_running']:
                    if item[1] == prompt_id:
                        logger.debug(f"Prompt {prompt_id} is currently being processed")
                        
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
    FLUX handler supporting both text-to-image and image-to-image
    Input format:
    {
        "input": {
            "prompt": "a beautiful landscape",
            "width": 1024,
            "height": 1024,
            "image": "base64_encoded_image"  # optional, for img2img
        }
    }
    """
    try:
        job_input = job['input']
        
        # Check for special actions
        action = job_input.get('action')
        if action == 'download_lora':
            # Handle LoRA download
            lora_url = job_input.get('lora_url')
            lora_name = job_input.get('lora_name', 'lora.safetensors')
            
            if not lora_url:
                return {"status": "error", "error": "No LoRA URL provided"}
            
            logger.info(f"Downloading LoRA: {lora_name} from {lora_url}")
            
            # Download to ComfyUI models directory
            import subprocess
            lora_path = f"/workspace/ComfyUI/models/loras/{lora_name}"
            
            # Use wget to download
            cmd = ['wget', '-O', lora_path, lora_url]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"LoRA downloaded successfully to {lora_path}")
                # Check file size
                import os
                size = os.path.getsize(lora_path) / (1024 * 1024)  # MB
                return {
                    "status": "success",
                    "message": f"LoRA downloaded successfully",
                    "path": lora_path,
                    "size_mb": round(size, 2)
                }
            else:
                logger.error(f"Failed to download LoRA: {result.stderr}")
                return {"status": "error", "error": f"Download failed: {result.stderr}"}
        
        # Normal image generation
        prompt = job_input.get('prompt', 'a beautiful landscape')
        width = job_input.get('width', 1024)
        height = job_input.get('height', 1024)
        
        # LoRA parameters
        lora_name = job_input.get('lora_name', None)
        lora_strength = job_input.get('lora_strength', 1.0)
        
        # Check for image input (base64)
        image_data = None
        is_img2img = False
        if 'image' in job_input and job_input['image']:
            try:
                image_data = base64.b64decode(job_input['image'])
                is_img2img = True
                logger.info("Image-to-image mode detected")
            except Exception as e:
                logger.warning(f"Failed to decode input image: {e}")
        
        # Log mode info
        mode_info = []
        if is_img2img:
            mode_info.append("img2img")
        if lora_name:
            mode_info.append(f"LoRA:{lora_name}")
        logger.info(f"Mode: {' + '.join(mode_info) if mode_info else 'txt2img'}")
        logger.info(f"Generating FLUX image: {prompt}")
        logger.info(f"Dimensions: {width}x{height}")
        
        # Load appropriate workflow
        workflow = handler.load_workflow(is_img2img=is_img2img, lora_name=lora_name)
        workflow = handler.update_prompt(workflow, prompt, width, height, image_data, lora_name, lora_strength)
        
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