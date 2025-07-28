#!/usr/bin/env python3
"""
Quick LoRA upload to RunPod using Firebase as intermediary
No SSH details needed!
"""

import os
import sys
import requests
import firebase_admin
from firebase_admin import credentials, storage, firestore
import uuid
from datetime import datetime

# Initialize Firebase (using existing app config)
if not firebase_admin._apps:
    # Use default credentials (assumes you're authenticated with Firebase CLI)
    firebase_admin.initialize_app()

def upload_lora_to_firebase(lora_path):
    """Upload LoRA to Firebase Storage temporarily"""
    if not os.path.exists(lora_path):
        print(f"❌ File not found: {lora_path}")
        return None
        
    if not lora_path.endswith('.safetensors'):
        print("❌ Only .safetensors files are supported")
        return None
        
    filename = os.path.basename(lora_path)
    file_size = os.path.getsize(lora_path) / (1024 * 1024)  # MB
    
    print(f"📁 Uploading: {filename} ({file_size:.2f} MB)")
    
    # Upload to Firebase Storage
    bucket = storage.bucket('amlwd-image-gen.appspot.com')
    blob_name = f'temp_loras/{uuid.uuid4()}/{filename}'
    blob = bucket.blob(blob_name)
    
    print("📤 Uploading to Firebase Storage...")
    blob.upload_from_filename(lora_path)
    
    # Make it public temporarily (we'll delete after transfer)
    blob.make_public()
    download_url = blob.public_url
    
    print("✅ Uploaded to Firebase!")
    
    # Create a Firestore document with download instructions
    db = firestore.client()
    doc_ref = db.collection('lora_uploads').document()
    doc_ref.set({
        'filename': filename,
        'download_url': download_url,
        'uploaded_at': datetime.now(),
        'status': 'pending',
        'blob_name': blob_name
    })
    
    print(f"\n📋 LoRA Upload Instructions:")
    print(f"1. SSH into your RunPod pod")
    print(f"2. Run this command:")
    print(f"\n   wget -O /workspace/ComfyUI/models/loras/{filename} '{download_url}'")
    print(f"\n3. Or run this to download and verify:")
    print(f"""
cd /workspace/ComfyUI/models/loras/
wget '{download_url}' -O {filename}
ls -la {filename}
""")
    
    print(f"\n4. The LoRA '{filename}' will be ready to use!")
    print(f"\n5. To use in generation, add to your request:")
    print(f'   "lora_name": "{filename}",')
    print(f'   "lora_strength": 1.0')
    
    # Optionally create a script file
    script_path = f"/tmp/download_lora_{filename}.sh"
    with open(script_path, 'w') as f:
        f.write(f"""#!/bin/bash
# Auto-generated LoRA download script
echo "Downloading {filename}..."
cd /workspace/ComfyUI/models/loras/
wget '{download_url}' -O {filename}
echo "Downloaded! Checking file..."
ls -la {filename}
echo "Done! LoRA is ready to use."
""")
    
    print(f"\n💡 Script created at: {script_path}")
    print(f"   Copy and run on your pod: bash download_lora_{filename}.sh")
    
    return download_url

def list_available_loras():
    """List LoRAs that might already be on the pod"""
    print("\n📂 Common LoRA locations on RunPod:")
    print("  /workspace/ComfyUI/models/loras/")
    print("  /runpod-volume/ComfyUI/models/loras/")
    print("\nTo check existing LoRAs, SSH to pod and run:")
    print("  ls -la /workspace/ComfyUI/models/loras/")

def main():
    print("🚀 Quick LoRA Upload for RunPod")
    print("-" * 50)
    
    if len(sys.argv) > 1:
        # Direct file upload
        lora_path = sys.argv[1]
        upload_lora_to_firebase(lora_path)
    else:
        # Interactive mode
        while True:
            print("\nOptions:")
            print("1. Upload a LoRA file")
            print("2. List LoRA locations")
            print("3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == '1':
                lora_path = input("Enter path to LoRA file: ").strip()
                if lora_path.startswith('"') and lora_path.endswith('"'):
                    lora_path = lora_path[1:-1]
                upload_lora_to_firebase(lora_path)
            elif choice == '2':
                list_available_loras()
            elif choice == '3':
                break
            else:
                print("Invalid option")
    
    print("\n👋 Done!")

if __name__ == "__main__":
    # Check if firebase-admin is installed
    try:
        import firebase_admin
    except ImportError:
        print("❌ firebase-admin not installed. Run: pip install firebase-admin")
        sys.exit(1)
    
    main()