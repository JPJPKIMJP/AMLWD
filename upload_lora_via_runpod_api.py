#!/usr/bin/env python3
"""
Upload LoRA files to RunPod volume via RunPod API
No SSH needed - uses RunPod's file upload API
"""

import os
import sys
import base64
import requests
import json
from pathlib import Path

# RunPod configuration - these should match your setup
RUNPOD_API_KEY = "YOUR_RUNPOD_API_KEY"  # Replace with your API key
RUNPOD_ENDPOINT_ID = "3s0v4wilu6dp30"   # Your FLUX endpoint

def upload_lora_to_runpod(lora_file_path):
    """Upload a LoRA file to RunPod using a temporary pod"""
    
    if not os.path.exists(lora_file_path):
        print(f"❌ File not found: {lora_file_path}")
        return False
    
    if not lora_file_path.endswith('.safetensors'):
        print("❌ Only .safetensors files are supported")
        return False
    
    filename = os.path.basename(lora_file_path)
    file_size = os.path.getsize(lora_file_path) / (1024 * 1024)  # MB
    
    print(f"📁 Uploading: {filename} ({file_size:.2f} MB)")
    print(f"🎯 Target: RunPod Endpoint {RUNPOD_ENDPOINT_ID}")
    
    # Read file and encode to base64
    print("📖 Reading file...")
    with open(lora_file_path, 'rb') as f:
        file_data = f.read()
        file_base64 = base64.b64encode(file_data).decode('utf-8')
    
    print("📤 Uploading to RunPod...")
    
    # Create a custom job that uploads the LoRA
    upload_job = {
        "input": {
            "action": "upload_lora",
            "filename": filename,
            "file_data": file_base64
        }
    }
    
    # Send to RunPod endpoint
    response = requests.post(
        f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
        headers={
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        },
        json=upload_job
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload job submitted! Job ID: {result.get('id')}")
        print("⏳ Waiting for upload to complete...")
        
        # Poll for completion
        job_id = result.get('id')
        while True:
            status_response = requests.get(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                if status['status'] == 'COMPLETED':
                    print("✅ LoRA uploaded successfully!")
                    return True
                elif status['status'] == 'FAILED':
                    print(f"❌ Upload failed: {status.get('error', 'Unknown error')}")
                    return False
            
            import time
            time.sleep(2)
    else:
        print(f"❌ Failed to submit upload job: {response.text}")
        return False

def create_simple_uploader():
    """Create a simpler upload script that modifies the handler temporarily"""
    
    script_content = '''#!/usr/bin/env python3
"""
Simple LoRA uploader using Firebase Storage
Uploads LoRA to Firebase and provides download link
"""

import os
import sys
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, storage as fb_storage
import datetime

# Initialize Firebase
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'amlwd-image-gen.appspot.com'
})

def upload_lora_to_firebase(lora_path):
    """Upload LoRA to Firebase Storage"""
    if not os.path.exists(lora_path):
        print(f"❌ File not found: {lora_path}")
        return None
        
    filename = os.path.basename(lora_path)
    
    # Upload to Firebase
    bucket = fb_storage.bucket()
    blob = bucket.blob(f'loras/{filename}')
    
    print(f"📤 Uploading {filename} to Firebase...")
    blob.upload_from_filename(lora_path)
    
    # Make it public
    blob.make_public()
    
    # Get URL
    url = blob.public_url
    print(f"✅ Uploaded! URL: {url}")
    
    print("\\n📋 Instructions:")
    print("1. SSH into your RunPod pod")
    print("2. Download the LoRA:")
    print(f"   wget -O /workspace/ComfyUI/models/loras/{filename} '{url}'")
    print("3. The LoRA is now ready to use!")
    
    return url

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_lora_firebase.py <lora_file>")
        sys.exit(1)
    
    upload_lora_to_firebase(sys.argv[1])
'''
    
    with open('/Users/jpsmac/AMLWD/upload_lora_firebase.py', 'w') as f:
        f.write(script_content)
    
    print("Created Firebase upload script at: /Users/jpsmac/AMLWD/upload_lora_firebase.py")

def main():
    print("🚀 RunPod LoRA Uploader")
    print("-" * 50)
    
    # Check API key
    if RUNPOD_API_KEY == "YOUR_RUNPOD_API_KEY":
        print("❌ Please set your RunPod API key in the script")
        print("   Edit line 16: RUNPOD_API_KEY = 'your_actual_key'")
        return
    
    # Alternative: Use environment variable
    api_key = os.environ.get('RUNPOD_API_KEY', RUNPOD_API_KEY)
    if not api_key or api_key == "YOUR_RUNPOD_API_KEY":
        print("❌ RunPod API key not found")
        print("   Set it in the script or use: export RUNPOD_API_KEY=your_key")
        return
    
    # Simple approach for now
    print("\n⚠️  Note: Direct upload via RunPod API requires handler modification.")
    print("Creating alternative upload method...\n")
    
    create_simple_uploader()
    
    print("\n📋 Quick Upload Method:")
    print("1. Use the web uploader on your pod:")
    print("   - SSH into pod: ssh root@<pod-ip>")
    print("   - Run: python3 /upload_lora.py")
    print("   - Access via RunPod proxy URL")
    print("\n2. Or use direct copy:")
    print("   - scp your_lora.safetensors root@<pod-ip>:/workspace/ComfyUI/models/loras/")
    print("\n3. Or use the Firebase method (created upload_lora_firebase.py)")

if __name__ == "__main__":
    main()