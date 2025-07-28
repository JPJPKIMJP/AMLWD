#!/usr/bin/env python3
"""
Deploy LoRA to RunPod pod
Automatically downloads LoRA files to the RunPod volume
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

# RunPod API configuration
RUNPOD_API_KEY = os.environ.get('RUNPOD_API_KEY')
RUNPOD_ENDPOINT_ID = os.environ.get('RUNPOD_ENDPOINT_ID')

def deploy_lora(lora_url, lora_name):
    """Deploy LoRA to RunPod by executing wget command via the endpoint"""
    
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        print("❌ Error: RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID environment variables must be set")
        print("\nSet them with:")
        print("export RUNPOD_API_KEY='your-api-key'")
        print("export RUNPOD_ENDPOINT_ID='your-endpoint-id'")
        return False
    
    print(f"🚀 Deploying LoRA: {lora_name}")
    print(f"📦 From URL: {lora_url}")
    
    # Create a special request that will trigger LoRA download
    payload = {
        "input": {
            "action": "download_lora",
            "lora_url": lora_url,
            "lora_name": lora_name
        }
    }
    
    try:
        # First, try to use the endpoint to download the LoRA
        print("\n📡 Sending download request to RunPod...")
        
        response = requests.post(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
            headers={
                "Authorization": f"Bearer {RUNPOD_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('id')
            print(f"✅ Job created: {job_id}")
            
            # Poll for completion
            print("\n⏳ Waiting for download to complete...")
            for i in range(60):  # Wait up to 5 minutes
                status_response = requests.get(
                    f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
                    headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    if status['status'] == 'COMPLETED':
                        print("\n✅ LoRA downloaded successfully!")
                        if status.get('output'):
                            print(f"📄 Output: {status['output']}")
                        return True
                    elif status['status'] == 'FAILED':
                        print(f"\n❌ Download failed: {status.get('error', 'Unknown error')}")
                        return False
                
                print(".", end="", flush=True)
                time.sleep(5)
            
            print("\n⚠️  Download timed out")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Fallback: provide manual instructions
    print("\n📋 Manual Instructions:")
    print("If automatic deployment failed, SSH into your RunPod pod and run:")
    print(f"\nwget -O /workspace/ComfyUI/models/loras/{lora_name} \"{lora_url}\"")
    print("\nOr if using volume mount:")
    print(f"wget -O /runpod-volume/ComfyUI/models/loras/{lora_name} \"{lora_url}\"")
    
    return False

def main():
    """Main function"""
    # The LoRA you just uploaded
    lora_url = "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753410944552_shiyuanlimei_v1.0.safetensors?alt=media&token=c1abf95f-1b20-422b-90fb-66347fe66367"
    lora_name = "shiyuanlimei_v1.0.safetensors"
    
    print("🎨 RunPod LoRA Deployment Tool")
    print("=" * 40)
    
    # Check if user wants to use a different LoRA
    use_default = input(f"\nDeploy {lora_name}? (Y/n): ").strip().lower()
    
    if use_default == 'n':
        lora_url = input("Enter LoRA URL: ").strip()
        lora_name = input("Enter LoRA filename: ").strip()
        if not lora_name.endswith('.safetensors'):
            lora_name += '.safetensors'
    
    # Deploy
    success = deploy_lora(lora_url, lora_name)
    
    if success:
        print("\n🎉 Deployment complete!")
        print(f"\nYou can now use this LoRA in your prompts with:")
        print(f"  lora_name: \"{lora_name[:-12]}\"")  # Remove .safetensors
        print(f"  lora_strength: 0.8")
    else:
        print("\n⚠️  Automatic deployment failed. Please use manual instructions above.")

if __name__ == "__main__":
    main()