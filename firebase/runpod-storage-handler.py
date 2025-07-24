"""
Example RunPod handler with volume storage for SDXL
This would replace/supplement the current RunPod endpoint
"""

import runpod
import torch
import base64
import io
import os
import json
from datetime import datetime
from diffusers import AutoPipelineForText2Image

# Volume mount path - RunPod mounts volumes at /workspace
VOLUME_PATH = "/workspace/persistent_storage"
IMAGES_PATH = f"{VOLUME_PATH}/images"
METADATA_PATH = f"{VOLUME_PATH}/metadata"

# Ensure directories exist
os.makedirs(IMAGES_PATH, exist_ok=True)
os.makedirs(METADATA_PATH, exist_ok=True)

# Load model
pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sdxl-turbo",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")

def save_to_volume(image, prompt, user_id, seed=None):
    """Save image to RunPod volume and return URL path"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{timestamp}_{seed or 'random'}.png"
    
    # Create user directory
    user_dir = os.path.join(IMAGES_PATH, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Save image
    image_path = os.path.join(user_dir, filename)
    image.save(image_path)
    
    # Save metadata
    metadata = {
        "prompt": prompt,
        "timestamp": timestamp,
        "filename": filename,
        "path": image_path,
        "seed": seed,
        "user_id": user_id
    }
    
    metadata_file = os.path.join(METADATA_PATH, f"{user_id}_{timestamp}.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f)
    
    # Return relative path that can be served
    return f"/images/{user_id}/{filename}"

def handler(job):
    """Handler function that saves to volume"""
    try:
        job_input = job['input']
        
        # Extract parameters
        prompt = job_input.get('prompt', '')
        user_id = job_input.get('user_id', 'anonymous')  # Pass from Firebase
        negative_prompt = job_input.get('negative_prompt', '')
        height = job_input.get('height', 768)  # Smaller default
        width = job_input.get('width', 768)
        num_inference_steps = job_input.get('num_inference_steps', 25)
        guidance_scale = job_input.get('guidance_scale', 7.5)
        seed = job_input.get('seed', None)
        
        # Generate image
        generator = None
        if seed is not None and seed != -1:
            generator = torch.Generator(device="cuda").manual_seed(seed)
        
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=height,
            width=width,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator
        ).images[0]
        
        # Save to volume
        volume_path = save_to_volume(image, prompt, user_id, seed)
        
        # Also create base64 for immediate display
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)  # JPEG for smaller size
        image_bytes = buffer.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Get storage stats
        user_dir = os.path.join(IMAGES_PATH, user_id)
        if os.path.exists(user_dir):
            user_images = len([f for f in os.listdir(user_dir) if f.endswith('.png')])
            total_size = sum(os.path.getsize(os.path.join(user_dir, f)) 
                           for f in os.listdir(user_dir)) / (1024 * 1024)  # MB
        else:
            user_images = 0
            total_size = 0
        
        return {
            "image": image_base64,
            "volume_path": volume_path,
            "seed": seed,
            "prompt": prompt,
            "storage_info": {
                "user_images": user_images,
                "total_size_mb": round(total_size, 2),
                "volume_available": os.path.exists(VOLUME_PATH)
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

# Optional: Add endpoint to retrieve images from volume
def get_image_handler(job):
    """Retrieve image from volume storage"""
    try:
        path = job['input'].get('path', '')
        full_path = os.path.join(IMAGES_PATH, path.lstrip('/images/'))
        
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                image_data = f.read()
            return {
                "image": base64.b64encode(image_data).decode('utf-8'),
                "success": True
            }
        else:
            return {"error": "Image not found", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

# Start the serverless worker
runpod.serverless.start({"handler": handler})