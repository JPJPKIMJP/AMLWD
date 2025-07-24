"""
RunPod Handler with Cloudflare R2 Integration
This replaces base64 responses with URL responses
"""

import runpod
import torch
import os
import boto3
from io import BytesIO
from datetime import datetime
import random
import string
from diffusers import AutoPipelineForText2Image

# Initialize R2 client (S3 compatible)
s3_client = boto3.client(
    's3',
    endpoint_url=os.environ.get('R2_ENDPOINT'),
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
    region_name='auto'  # R2 uses 'auto' for region
)

# Load SDXL model
pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sdxl-turbo",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")

def generate_unique_id():
    """Generate a unique ID for the image"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}_{random_str}"

def upload_to_r2(image, job_id, image_index):
    """Upload image to R2 and return public URL"""
    try:
        # Convert PIL image to bytes
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        
        # Generate unique filename
        filename = f"images/{job_id}/{generate_unique_id()}_{image_index}.png"
        
        # Upload to R2
        s3_client.put_object(
            Bucket=os.environ.get('R2_BUCKET'),
            Key=filename,
            Body=buffer.getvalue(),
            ContentType='image/png',
            CacheControl='public, max-age=3600'  # Cache for 1 hour
        )
        
        # Construct public URL
        # R2 public URL format: https://pub-[hash].r2.dev/[key]
        public_base = os.environ.get('R2_PUBLIC_URL', '').rstrip('/')
        public_url = f"{public_base}/{filename}"
        
        return public_url
        
    except Exception as e:
        print(f"Error uploading to R2: {str(e)}")
        raise

def handler(job):
    """Handler function that uploads to R2 instead of returning base64"""
    try:
        job_input = job['input']
        job_id = job.get('id', 'unknown')
        
        # Extract parameters
        prompt = job_input.get('prompt', '')
        negative_prompt = job_input.get('negative_prompt', '')
        width = job_input.get('width', 768)  # Default to 768 for better success
        height = job_input.get('height', 768)
        num_inference_steps = job_input.get('num_inference_steps', 25)
        guidance_scale = job_input.get('guidance_scale', 7.5)
        num_images = job_input.get('num_images', 1)
        seed = job_input.get('seed', None)
        
        # Set up generator for reproducible results
        generator = None
        if seed is not None and seed != -1:
            generator = torch.Generator(device="cuda").manual_seed(seed)
        
        # Generate images
        print(f"Generating {num_images} images for prompt: {prompt[:50]}...")
        
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            num_images_per_prompt=num_images,
            generator=generator
        )
        
        # Upload all images to R2 and collect URLs
        image_urls = []
        for i, image in enumerate(result.images):
            print(f"Uploading image {i+1}/{num_images} to R2...")
            url = upload_to_r2(image, job_id, i)
            image_urls.append(url)
            print(f"Uploaded: {url}")
        
        # Return URLs instead of base64!
        # This response will be tiny (just URLs), avoiding the 10MB limit
        return {
            "status": "success",
            "images": image_urls,
            "count": len(image_urls),
            "seed": seed,
            "message": f"Generated {len(image_urls)} images successfully"
        }
        
    except Exception as e:
        print(f"Error in handler: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate images"
        }

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})