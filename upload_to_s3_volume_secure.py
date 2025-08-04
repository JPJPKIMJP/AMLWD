#!/usr/bin/env python3
"""
Upload LoRA files to RunPod S3 volume using Firebase credentials
More secure version that fetches credentials from Firebase
"""

import boto3
from botocore.config import Config
import os
import sys
import requests
from pathlib import Path

def get_s3_credentials():
    """Fetch S3 credentials from Firebase"""
    
    # You need to set your RUNPOD_API_KEY
    api_key = os.environ.get('RUNPOD_API_KEY')
    if not api_key:
        print("Error: Please set RUNPOD_API_KEY environment variable")
        print("export RUNPOD_API_KEY=your_runpod_api_key")
        return None
    
    firebase_url = 'https://us-central1-amlwd-image-gen.cloudfunctions.net/getS3Credentials'
    
    try:
        response = requests.get(
            firebase_url,
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching credentials: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_s3_client(credentials):
    """Create S3 client with credentials"""
    
    config = Config(
        region_name='US-KS-2',
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
    
    return boto3.client(
        's3',
        endpoint_url=credentials['S3_ENDPOINT'],
        aws_access_key_id=credentials['S3_ACCESS_KEY'],
        aws_secret_access_key=credentials['S3_SECRET_KEY'],
        config=config
    )

def upload_lora_to_s3(file_path, lora_name=None):
    """Upload a LoRA file to S3 volume"""
    
    # Get credentials
    creds = get_s3_credentials()
    if not creds:
        return False
    
    s3_client = create_s3_client(creds)
    bucket = creds['S3_BUCKET']
    
    # Get file name
    if lora_name is None:
        lora_name = os.path.basename(file_path)
    
    # Ensure .safetensors extension
    if not lora_name.endswith('.safetensors'):
        lora_name += '.safetensors'
    
    # S3 key path
    key = f"models/loras/{lora_name}"
    
    print(f"Uploading {file_path} to s3://{bucket}/{key}")
    
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
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType='application/octet-stream'
            )
        
        print(f"✅ Successfully uploaded to S3 volume!")
        print(f"   Path in volume: /runpod-volume/{key}")
        
        # Verify upload
        response = s3_client.head_object(Bucket=bucket, Key=key)
        uploaded_size = response['ContentLength'] / (1024 * 1024)
        print(f"   Verified: {uploaded_size:.1f} MB uploaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading: {e}")
        return False

def list_loras_in_s3():
    """List all LoRAs currently in S3 volume"""
    
    # Get credentials
    creds = get_s3_credentials()
    if not creds:
        return
    
    s3_client = create_s3_client(creds)
    bucket = creds['S3_BUCKET']
    
    print("\nLoRAs in S3 volume:")
    print("-" * 50)
    
    try:
        # List objects in models/loras/
        response = s3_client.list_objects_v2(
            Bucket=bucket,
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
    
    # Get credentials
    creds = get_s3_credentials()
    if not creds:
        return False
    
    s3_client = create_s3_client(creds)
    bucket = creds['S3_BUCKET']
    
    # Ensure .safetensors extension
    if not lora_name.endswith('.safetensors'):
        lora_name += '.safetensors'
    
    # Default output path
    if output_path is None:
        output_path = lora_name
    
    key = f"models/loras/{lora_name}"
    
    print(f"Downloading {lora_name} from S3 volume...")
    
    try:
        s3_client.download_file(bucket, key, output_path)
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Downloaded {lora_name} ({file_size:.1f} MB) to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return False

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Secure S3 Volume Manager (fetches credentials from Firebase)")
        print("\nUsage:")
        print("  Upload:   python upload_to_s3_volume_secure.py upload <file_path> [lora_name]")
        print("  List:     python upload_to_s3_volume_secure.py list")
        print("  Download: python upload_to_s3_volume_secure.py download <lora_name> [output_path]")
        print("\nFirst set your RunPod API key:")
        print("  export RUNPOD_API_KEY=your_runpod_api_key")
        print("\nExamples:")
        print("  python upload_to_s3_volume_secure.py upload korean_lora.safetensors")
        print("  python upload_to_s3_volume_secure.py list")
        print("  python upload_to_s3_volume_secure.py download korean_lora")
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