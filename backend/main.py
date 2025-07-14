from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import aiohttp
import asyncio
import base64
import os
from datetime import datetime
import uuid

app = FastAPI(title="AI Image Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")

class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    width: Optional[int] = 512
    height: Optional[int] = 512
    num_inference_steps: Optional[int] = 20
    guidance_scale: Optional[float] = 7.5
    seed: Optional[int] = -1

class GenerationStatus(BaseModel):
    job_id: str
    status: str
    created_at: str
    result: Optional[dict] = None

jobs = {}

@app.get("/")
async def root():
    return {"message": "AI Image Generation API", "version": "1.0.0"}

@app.post("/generate")
async def generate_image(request: ImageGenerationRequest, background_tasks: BackgroundTasks):
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise HTTPException(status_code=500, detail="RunPod credentials not configured")
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "request": request.dict()
    }
    
    background_tasks.add_task(call_runpod, job_id, request)
    
    return {"job_id": job_id, "status": "pending"}

async def call_runpod(job_id: str, request: ImageGenerationRequest):
    url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": request.dict()
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    jobs[job_id]["status"] = "completed"
                    jobs[job_id]["result"] = result.get("output", {})
                else:
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error"] = result.get("error", "Unknown error")
                    
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/jobs")
async def list_jobs():
    return list(jobs.keys())

@app.post("/test-local")
async def test_local_generation(request: ImageGenerationRequest):
    """Test endpoint that returns a placeholder image for local development"""
    
    placeholder_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    return {
        "image_base64": placeholder_image,
        "seed": request.seed if request.seed != -1 else 12345,
        "prompt": request.prompt,
        "width": request.width,
        "height": request.height
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)