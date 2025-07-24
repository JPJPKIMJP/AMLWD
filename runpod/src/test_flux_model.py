#!/usr/bin/env python3
"""
Test script to verify FLUX model accessibility in RunPod
"""

import os
import json

def test_model_access():
    print("=== FLUX Model Test ===")
    
    # Check diffusion_models directory
    diffusion_models_paths = [
        "/ComfyUI/models/diffusion_models",
        "/runpod-volume/ComfyUI/models/diffusion_models",
        "/workspace/ComfyUI/models/diffusion_models"
    ]
    
    flux_model = "flux1-dev-kontext_fp8_scaled.safetensors"
    
    for path in diffusion_models_paths:
        full_path = os.path.join(path, flux_model)
        if os.path.exists(full_path):
            size_gb = os.path.getsize(full_path) / (1024**3)
            print(f"✓ FLUX model FOUND at: {full_path}")
            print(f"  Size: {size_gb:.2f} GB")
            
            # Check if it's readable
            try:
                with open(full_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB
                print("  ✓ File is readable")
            except Exception as e:
                print(f"  ✗ File read error: {e}")
        else:
            print(f"✗ Not found at: {full_path}")
    
    # Test minimal workflow
    print("\n=== Testing Minimal Workflow ===")
    workflow = {
        "1": {
            "inputs": {
                "unet_name": flux_model,
                "weight_dtype": "default"
            },
            "class_type": "UNETLoader"
        }
    }
    
    print("Workflow JSON:")
    print(json.dumps(workflow, indent=2))
    
    # Try to load via ComfyUI API
    try:
        import requests
        response = requests.post(
            "http://localhost:8188/prompt",
            json={"prompt": workflow}
        )
        print(f"\nComfyUI Response: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"\nComfyUI request failed: {e}")

if __name__ == "__main__":
    test_model_access()