#!/usr/bin/env python3
"""
Upload LoRA files directly to RunPod S3 volume
"""

import boto3
from botocore.config import Config
import os
import sys
from pathlib import Path

# S3 configuration
S3_ENDPOINT = "https://s3api-us-ks-2.runpod.io"
S3_BUCKET = "82elxnhs55"
S3_ACCESS_KEY = "user_2zH4PpHJhiBtUPAk4NUr6fhk3YG"
S3_SECRET_KEY = "rps_188FHICZ3JLSLYHHLAPAGG6X9DWQ5JU940ZIWM081subkx"

def upload_lora_to_s3(file_path, lora_name=None):
    """Upload a LoRA file to S3 volume"""
    
    # Create S3 client with custom config
    config = Config(
        region_name='US-KS-2',
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
    
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=config
    )
    
    # Get file name
    if lora_name is None:
        lora_name = os.path.basename(file_path)
    
    # Ensure .safetensors extension
    if not lora_name.endswith('.safetensors'):
        lora_name += '.safetensors'
    
    # S3 key path
    key = f"models/loras/{lora_name}"
    
    print(f"Uploading {file_path} to s3://{S3_BUCKET}/{key}")
    
    try:
        # Check if file exists locally
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found")
            return False
        
        # Get file size
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"File size: {file_size:.1f} MB")
        
        # Upload file
        with open(file_path, 'rb') as f:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=f,
                ContentType='application/octet-stream'
            )
        
        print(f"✅ Successfully uploaded to S3 volume!")
        print(f"   Path in volume: /runpod-volume/{key}")
        
        # Verify upload
        response = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        uploaded_size = response['ContentLength'] / (1024 * 1024)
        print(f"   Verified: {uploaded_size:.1f} MB uploaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading: {e}")
        return False

def list_loras_in_s3():
    """List all LoRAs currently in S3 volume"""
    
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
    
    print("\nLoRAs in S3 volume:")
    print("-" * 50)
    
    try:
        # List objects in models/loras/
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='models/loras/'
        )
        
        if 'Contents' not in response:
            print("No LoRAs found in volume")
            return
        
        total_size = 0
        for obj in response['Contents']:
            name = obj['Key'].replace('models/loras/', '')
            size = obj['Size'] / (1024 * 1024)  # MB
            total_size += size
            print(f"  • {name} ({size:.1f} MB)")
        
        print(f"\nTotal: {len(response['Contents'])} LoRAs, {total_size:.1f} MB")
        
    except Exception as e:
        print(f"Error listing LoRAs: {e}")

def download_lora_from_s3(lora_name, output_path=None):
    """Download a LoRA from S3 volume"""
    
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
    
    # Ensure .safetensors extension
    if not lora_name.endswith('.safetensors'):
        lora_name += '.safetensors'
    
    # Default output path
    if output_path is None:
        output_path = lora_name
    
    key = f"models/loras/{lora_name}"
    
    print(f"Downloading {lora_name} from S3 volume...")
    
    try:
        s3_client.download_file(S3_BUCKET, key, output_path)
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Downloaded {lora_name} ({file_size:.1f} MB) to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return False

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Upload:   python upload_to_s3_volume.py upload <file_path> [lora_name]")
        print("  List:     python upload_to_s3_volume.py list")
        print("  Download: python upload_to_s3_volume.py download <lora_name> [output_path]")
        print("\nExamples:")
        print("  python upload_to_s3_volume.py upload korean_lora.safetensors")
        print("  python upload_to_s3_volume.py upload /path/to/lora.bin my_custom_lora")
        print("  python upload_to_s3_volume.py list")
        print("  python upload_to_s3_volume.py download korean_lora")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "upload":
        if len(sys.argv) < 3:
            print("Error: Please provide file path")
            sys.exit(1)
        
        file_path = sys.argv[2]
        lora_name = sys.argv[3] if len(sys.argv) > 3 else None
        
        success = upload_lora_to_s3(file_path, lora_name)
        sys.exit(0 if success else 1)
    
    elif command == "list":
        list_loras_in_s3()
    
    elif command == "download":
        if len(sys.argv) < 3:
            print("Error: Please provide LoRA name")
            sys.exit(1)
        
        lora_name = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        success = download_lora_from_s3(lora_name, output_path)
        sys.exit(0 if success else 1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()