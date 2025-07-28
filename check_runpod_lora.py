#!/usr/bin/env python3
"""
Check if LoRA is available on RunPod
"""
import requests
import os
import sys

# You need to set these environment variables
RUNPOD_API_KEY = os.environ.get('RUNPOD_API_KEY')
RUNPOD_ENDPOINT_ID = os.environ.get('RUNPOD_ENDPOINT_ID')

if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
    print("❌ Please set environment variables:")
    print("export RUNPOD_API_KEY='your-api-key'")
    print("export RUNPOD_ENDPOINT_ID='your-endpoint-id'")
    sys.exit(1)

print("🔍 Checking RunPod endpoint status...")

# Check endpoint health
response = requests.get(
    f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/health",
    headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
)

if response.status_code == 200:
    print("✅ RunPod endpoint is healthy")
    
    # Test generation with LoRA
    print("\n🧪 Testing generation with LoRA...")
    test_response = requests.post(
        f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync",
        headers={
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": {
                "prompt": "anime girl with blue hair",
                "width": 512,
                "height": 512,
                "lora_name": "shiyuanlimei_v1.0",
                "lora_strength": 0.8
            }
        },
        timeout=300
    )
    
    if test_response.status_code == 200:
        result = test_response.json()
        if result.get('status') == 'COMPLETED':
            print("✅ LoRA test successful!")
        else:
            print(f"⚠️  Status: {result.get('status')}")
            print(f"Details: {result}")
    else:
        print(f"❌ Test failed: {test_response.status_code}")
        print(test_response.text)
else:
    print(f"❌ Endpoint not accessible: {response.status_code}")

print("\n📝 Manual download command for SSH:")
print('wget -O /workspace/ComfyUI/models/loras/shiyuanlimei_v1.0.safetensors "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753410944552_shiyuanlimei_v1.0.safetensors?alt=media&token=c1abf95f-1b20-422b-90fb-66347fe66367"')