#!/usr/bin/env python3
"""
Quick LoRA deployment using RunPod API
"""
import requests
import os
import time
import sys

# Get RunPod credentials from environment variables
RUNPOD_API_KEY = os.environ.get('RUNPOD_API_KEY')
RUNPOD_ENDPOINT_ID = os.environ.get('RUNPOD_ENDPOINT_ID')

if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
    print("❌ Error: Missing RunPod credentials")
    print("\nPlease set environment variables:")
    print("export RUNPOD_API_KEY='your-api-key'")
    print("export RUNPOD_ENDPOINT_ID='your-endpoint-id'")
    sys.exit(1)

# The LoRA to deploy
LORA_URL = "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753410944552_shiyuanlimei_v1.0.safetensors?alt=media&token=c1abf95f-1b20-422b-90fb-66347fe66367"
LORA_NAME = "shiyuanlimei_v1.0.safetensors"

print("🚀 Deploying LoRA to RunPod...")
print(f"📦 LoRA: {LORA_NAME}")

# Send download request
response = requests.post(
    f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
    headers={
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "input": {
            "action": "download_lora",
            "lora_url": LORA_URL,
            "lora_name": LORA_NAME
        }
    }
)

if response.status_code == 200:
    result = response.json()
    job_id = result.get('id')
    print(f"✅ Job created: {job_id}")
    
    # Poll for completion
    print("⏳ Downloading...", end="", flush=True)
    for i in range(60):
        time.sleep(5)
        print(".", end="", flush=True)
        
        status_response = requests.get(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
            headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
        )
        
        if status_response.status_code == 200:
            status = status_response.json()
            if status['status'] == 'COMPLETED':
                print("\n✅ LoRA downloaded successfully!")
                output = status.get('output', {})
                print(f"📄 Path: {output.get('path')}")
                print(f"📊 Size: {output.get('size_mb')} MB")
                print("\n🎉 You can now use this LoRA with:")
                print(f'   lora_name: "shiyuanlimei_v1.0"')
                print(f'   lora_strength: 0.8')
                break
            elif status['status'] == 'FAILED':
                print(f"\n❌ Failed: {status.get('error')}")
                break
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)