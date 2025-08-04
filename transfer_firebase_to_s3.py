#!/usr/bin/env python3
"""
Transfer LoRA from Firebase Storage to RunPod S3 volume
"""

import requests
import boto3
from botocore.config import Config
import os
import sys

def download_from_url(url, filename):
    """Download file from URL"""
    print(f"Downloading from: {url[:100]}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\rProgress: {percent:.1f}%", end='')
    print("\nDownload complete!")
    return filename

def upload_to_s3(local_file, s3_key):
    """Upload file to S3"""
    config = Config(
        region_name='US-KS-2',
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
    
    s3 = boto3.client(
        's3',
        endpoint_url='https://s3api-us-ks-2.runpod.io',
        aws_access_key_id='user_2zH4PpHJhiBtUPAk4NUr6fhk3YG',
        aws_secret_access_key='rps_188FHICZ3JLSLYHHLAPAGG6X9DWQ5JU940ZIWM081subkx',
        config=config
    )
    
    file_size = os.path.getsize(local_file) / (1024 * 1024)
    print(f"\nUploading {file_size:.1f}MB to S3: {s3_key}")
    
    with open(local_file, 'rb') as f:
        s3.put_object(
            Bucket='82elxnhs55',
            Key=s3_key,
            Body=f,
            ContentType='application/octet-stream'
        )
    
    print("Upload complete!")
    
    # Verify
    response = s3.head_object(Bucket='82elxnhs55', Key=s3_key)
    print(f"Verified in S3: {response['ContentLength']/1024/1024:.1f}MB")

def main():
    if len(sys.argv) < 3:
        print("Usage: python transfer_firebase_to_s3.py <firebase_url> <lora_name>")
        print("Example: python transfer_firebase_to_s3.py 'https://firebasestorage...' 'nsfw_v2'")
        sys.exit(1)
    
    firebase_url = sys.argv[1]
    lora_name = sys.argv[2]
    
    # Ensure .safetensors extension
    if not lora_name.endswith('.safetensors'):
        lora_name += '.safetensors'
    
    # S3 key path (corrected path)
    s3_key = f"ComfyUI/models/loras/{lora_name}"
    
    # Temporary local file
    temp_file = f"/tmp/{lora_name}"
    
    try:
        # Download from Firebase
        download_from_url(firebase_url, temp_file)
        
        # Upload to S3
        upload_to_s3(temp_file, s3_key)
        
        # Cleanup
        os.remove(temp_file)
        print(f"\n✅ Successfully transferred {lora_name} to RunPod S3 volume!")
        print(f"   S3 path: {s3_key}")
        print(f"   Container path: /runpod-volume/{s3_key}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        sys.exit(1)

if __name__ == "__main__":
    main()