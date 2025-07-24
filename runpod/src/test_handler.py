#!/usr/bin/env python3
"""
Simple test handler to debug FLUX model issues
"""

import runpod
import os
import json

def test_handler(job):
    """Test handler that just checks model availability"""
    
    result = {
        "diffusion_models_exists": os.path.exists("/ComfyUI/models/diffusion_models"),
        "models_in_diffusion": [],
        "flux_model_found": False,
        "comfyui_test": None
    }
    
    # Check diffusion_models
    if os.path.exists("/ComfyUI/models/diffusion_models"):
        result["models_in_diffusion"] = os.listdir("/ComfyUI/models/diffusion_models")[:5]
        flux_path = "/ComfyUI/models/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors"
        result["flux_model_found"] = os.path.exists(flux_path)
        
        if result["flux_model_found"]:
            result["flux_model_size_gb"] = os.path.getsize(flux_path) / (1024**3)
    
    # Test minimal ComfyUI request
    try:
        import requests
        # Just test if ComfyUI is running
        response = requests.get("http://localhost:8188/system_stats")
        result["comfyui_running"] = response.status_code == 200
        
        # Try minimal workflow
        if result["comfyui_running"]:
            workflow = {
                "1": {
                    "inputs": {
                        "unet_name": "flux1-dev-kontext_fp8_scaled.safetensors",
                        "weight_dtype": "default"
                    },
                    "class_type": "UNETLoader"
                }
            }
            prompt_response = requests.post(
                "http://localhost:8188/prompt",
                json={"prompt": workflow}
            )
            result["comfyui_test"] = {
                "status": prompt_response.status_code,
                "response": prompt_response.text[:500]  # First 500 chars
            }
    except Exception as e:
        result["comfyui_error"] = str(e)
    
    return result

# Start RunPod handler
runpod.serverless.start({"handler": test_handler})