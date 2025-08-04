#!/usr/bin/env python3
"""
Pre-load LoRAs from Firebase Storage to RunPod S3 volume
This ensures LoRAs are ready to use without downloading during generation
"""

import json
import requests
import boto3
from botocore.config import Config
import os
import sys
from datetime import datetime

# S3 Configuration
S3_CONFIG = {
    'endpoint': 'https://s3api-us-ks-2.runpod.io',
    'access_key': 'user_2zH4PpHJhiBtUPAk4NUr6fhk3YG',
    'secret_key': 'rps_188FHICZ3JLSLYHHLAPAGG6X9DWQ5JU940ZIWM081subkx',
    'bucket': '82elxnhs55',
    'region': 'US-KS-2'
}

def create_s3_client():
    """Create S3 client with proper configuration"""
    config = Config(
        region_name=S3_CONFIG['region'],
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
    
    return boto3.client(
        's3',
        endpoint_url=S3_CONFIG['endpoint'],
        aws_access_key_id=S3_CONFIG['access_key'],
        aws_secret_access_key=S3_CONFIG['secret_key'],
        config=config
    )

def download_from_url(url, local_path):
    """Download file from URL with progress"""
    print(f"Downloading from Firebase Storage...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    print("\n✓ Download complete")
    return downloaded

def check_s3_exists(s3_client, key):
    """Check if file already exists in S3"""
    try:
        response = s3_client.head_object(Bucket=S3_CONFIG['bucket'], Key=key)
        return True, response['ContentLength']
    except:
        return False, 0

def upload_to_s3(s3_client, local_path, s3_key):
    """Upload file to S3"""
    file_size = os.path.getsize(local_path)
    print(f"Uploading {file_size/1024/1024:.1f}MB to S3...")
    
    with open(local_path, 'rb') as f:
        s3_client.put_object(
            Bucket=S3_CONFIG['bucket'],
            Key=s3_key,
            Body=f,
            ContentType='application/octet-stream'
        )
    
    print(f"✓ Uploaded to S3: {s3_key}")

def preload_lora(firebase_url, lora_name):
    """Pre-load a single LoRA from Firebase to S3"""
    # Ensure .safetensors extension
    if not lora_name.endswith('.safetensors'):
        lora_name += '.safetensors'
    
    # S3 key path
    s3_key = f"ComfyUI/models/loras/{lora_name}"
    
    # Create S3 client
    s3_client = create_s3_client()
    
    # Check if already exists in S3
    exists, size = check_s3_exists(s3_client, s3_key)
    if exists:
        print(f"✓ LoRA already exists in S3: {lora_name} ({size/1024/1024:.1f}MB)")
        return True
    
    # Download from Firebase
    temp_path = f"/tmp/{lora_name}"
    try:
        size = download_from_url(firebase_url, temp_path)
        
        # Check if it's a FLUX LoRA
        size_mb = size / 1024 / 1024
        if size_mb < 200:
            print(f"⚠️  Warning: File size ({size_mb:.1f}MB) suggests this might be an SD1.5 LoRA, not FLUX")
        
        # Upload to S3
        upload_to_s3(s3_client, temp_path, s3_key)
        
        # Cleanup
        os.remove(temp_path)
        
        print(f"✅ Successfully pre-loaded {lora_name} to RunPod S3 volume!")
        print(f"   It will be available at: /runpod-volume/{s3_key}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def preload_from_localstorage(localstorage_json):
    """Pre-load all LoRAs from localStorage export"""
    try:
        custom_loras = json.loads(localstorage_json)
        
        print(f"Found {len(custom_loras)} LoRAs to pre-load")
        print("=" * 60)
        
        success_count = 0
        for key, lora_data in custom_loras.items():
            print(f"\nProcessing: {lora_data['name']}")
            if 'url' in lora_data:
                if preload_lora(lora_data['url'], key):
                    success_count += 1
            else:
                print("  No URL found, skipping")
        
        print("\n" + "=" * 60)
        print(f"Pre-loaded {success_count}/{len(custom_loras)} LoRAs successfully!")
        
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")
    except Exception as e:
        print(f"Error: {e}")

def list_s3_loras():
    """List all LoRAs currently in S3"""
    s3_client = create_s3_client()
    
    print("\nLoRAs in RunPod S3 volume:")
    print("-" * 60)
    
    response = s3_client.list_objects_v2(
        Bucket=S3_CONFIG['bucket'],
        Prefix='ComfyUI/models/loras/'
    )
    
    if 'Contents' not in response:
        print("No LoRAs found")
        return
    
    total_size = 0
    for obj in response['Contents']:
        name = obj['Key'].split('/')[-1]
        size = obj['Size'] / 1024 / 1024
        total_size += size
        modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"  • {name} ({size:.1f}MB) - {modified}")
    
    print(f"\nTotal: {len(response['Contents'])} LoRAs, {total_size:.1f}MB")

def main():
    if len(sys.argv) < 2:
        print("Pre-load LoRAs to RunPod S3 Volume")
        print("\nUsage:")
        print("  Single LoRA:  python preload_loras_to_s3.py <firebase_url> <lora_name>")
        print("  From browser: python preload_loras_to_s3.py browser")
        print("  List LoRAs:   python preload_loras_to_s3.py list")
        print("\nTo pre-load from browser:")
        print("  1. Open your web app")
        print("  2. In browser console run: copy(JSON.stringify(JSON.parse(localStorage.getItem('customLoras'))))")
        print("  3. Run: python preload_loras_to_s3.py browser")
        print("  4. Paste the JSON when prompted")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_s3_loras()
    
    elif command == 'browser':
        print("Paste the localStorage JSON (Ctrl+D when done):")
        import sys
        json_data = sys.stdin.read()
        preload_from_localstorage(json_data)
    
    else:
        # Single LoRA mode
        if len(sys.argv) < 3:
            print("Error: Please provide both URL and LoRA name")
            sys.exit(1)
        
        firebase_url = sys.argv[1]
        lora_name = sys.argv[2]
        preload_lora(firebase_url, lora_name)

if __name__ == "__main__":
    main()