import runpod
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import base64
from io import BytesIO
import os
import time

device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = None

def load_model():
    global pipe
    if pipe is None:
        model_id = os.environ.get('MODEL_ID', 'runwayml/stable-diffusion-v1-5')
        
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            safety_checker=None,
            requires_safety_checker=False
        )
        
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe = pipe.to(device)
        
        if device == "cuda":
            pipe.enable_attention_slicing()
            pipe.enable_vae_slicing()
            
        print(f"Model loaded: {model_id}")

def handler(job):
    """
    RunPod serverless handler function
    Input format:
    {
        "input": {
            "prompt": "a beautiful sunset over mountains",
            "negative_prompt": "ugly, blurry, low quality",
            "width": 512,
            "height": 512,
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
            "seed": -1
        }
    }
    """
    try:
        job_input = job['input']
        
        prompt = job_input.get('prompt', '')
        if not prompt:
            return {"error": "No prompt provided"}
            
        load_model()
        
        negative_prompt = job_input.get('negative_prompt', '')
        width = job_input.get('width', 512)
        height = job_input.get('height', 512)
        num_inference_steps = job_input.get('num_inference_steps', 20)
        guidance_scale = job_input.get('guidance_scale', 7.5)
        seed = job_input.get('seed', -1)
        
        if seed == -1:
            seed = int(time.time())
            
        generator = torch.Generator(device=device).manual_seed(seed)
        
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator
        ).images[0]
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {
            "image_base64": image_base64,
            "seed": seed,
            "prompt": prompt,
            "width": width,
            "height": height
        }
        
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})