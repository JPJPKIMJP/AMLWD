#!/usr/bin/env python3
"""
Test script to download a LoRA to RunPod automatically
"""

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Your RunPod credentials
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_ENDPOINT_ID = os.getenv('RUNPOD_ENDPOINT_ID')

def download_lora_to_runpod(lora_url, lora_name):
    """Download a LoRA directly to RunPod server"""
    
    print(f"🚀 Downloading LoRA to RunPod")
    print(f"📦 Name: {lora_name}")
    print(f"🔗 URL: {lora_url}")
    
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
                "lora_url": lora_url,
                "lora_name": lora_name
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        job_id = result.get('id')
        print(f"✅ Job created: {job_id}")
        
        # Poll for completion
        print("⏳ Downloading...", end="", flush=True)
        for i in range(30):  # 2.5 minutes max
            time.sleep(5)
            print(".", end="", flush=True)
            
            # Check status
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
                    print(f"\n🎉 You can now use this LoRA with:")
                    print(f'   "lora_name": "{lora_name}"')
                    print(f'   "lora_strength": 0.8')
                    return True
                elif status['status'] == 'FAILED':
                    print(f"\n❌ Failed: {status.get('error')}")
                    return False
        
        print("\n⏱️ Timeout waiting for download")
        return False
    else:
        print(f"❌ Failed to create job: {response.status_code}")
        print(response.text)
        return False

# Example usage
if __name__ == "__main__":
    # Test with a known LoRA
    test_lora_url = "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753410944552_shiyuanlimei_v1.0.safetensors?alt=media&token=c1abf95f-1b20-422b-90fb-66347fe66367"
    test_lora_name = "shiyuanlimei_v1.0.safetensors"
    
    download_lora_to_runpod(test_lora_url, test_lora_name)