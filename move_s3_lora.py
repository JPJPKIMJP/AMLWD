#!/usr/bin/env python3
"""
Move LoRA file to correct path in S3
"""

import boto3
from botocore.config import Config

# S3 configuration
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

bucket = '82elxnhs55'
old_key = 'models/loras/nsfw_v2.safetensors'
new_key = 'ComfyUI/models/loras/nsfw_v2.safetensors'

print(f"Moving {old_key} to {new_key}")

try:
    # Copy to new location
    copy_source = {'Bucket': bucket, 'Key': old_key}
    s3.copy_object(CopySource=copy_source, Bucket=bucket, Key=new_key)
    print(f"✓ Copied to {new_key}")
    
    # Delete from old location
    s3.delete_object(Bucket=bucket, Key=old_key)
    print(f"✓ Deleted from {old_key}")
    
    # Verify new location
    response = s3.head_object(Bucket=bucket, Key=new_key)
    print(f"✓ Verified at new location: {response['ContentLength']/1024/1024:.1f}MB")
    
except Exception as e:
    print(f"Error: {e}")