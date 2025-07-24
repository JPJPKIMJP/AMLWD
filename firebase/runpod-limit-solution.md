# RunPod 10MB Response Limit - The Real Issue

## The Problem
RunPod serverless has a **fixed 10MB limit** on both `/run` and `/runsync` endpoints. This is not configurable and cannot be changed by users.

### Why batches fail:
- Base64 encoding adds ~33% overhead
- Each 768x768 PNG image ≈ 1.5-2MB base64
- 4 images × 2MB = 8MB + overhead > 10MB limit
- RunPod returns: "Failed to return job results | 400 Bad Request"

## Current Workaround
We allow up to 4 images but warn users:
- **1-2 images**: Can use up to 1024x1024
- **3-4 images**: Should use 512x512 or 768x768

## Proper Solution (Requires RunPod Endpoint Changes)

### Option 1: Upload to Cloud Storage from RunPod
```python
# In RunPod handler
import boto3
from io import BytesIO

def handler(job):
    # Generate images
    images = generate_images(...)
    
    # Upload to S3/Cloud Storage
    urls = []
    for i, image in enumerate(images):
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Upload to S3
        s3_key = f"temp/{job_id}/image_{i}.png"
        s3_client.put_object(Bucket='bucket', Key=s3_key, Body=buffer)
        
        # Generate presigned URL (expires in 1 hour)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'bucket', 'Key': s3_key},
            ExpiresIn=3600
        )
        urls.append(url)
    
    # Return URLs instead of base64
    return {"image_urls": urls, "count": len(urls)}
```

### Option 2: Use RunPod's Built-in Upload
```python
from runpod.serverless.utils import upload_file_to_bucket

def handler(job):
    images = generate_images(...)
    urls = []
    
    for image in images:
        # RunPod's built-in upload function
        url = upload_file_to_bucket(
            file_data=image_to_bytes(image),
            file_name=f"image_{uuid4()}.png"
        )
        urls.append(url)
    
    return {"image_urls": urls}
```

### Option 3: Split Large Batches
Generate images one at a time with multiple API calls instead of batching.

## Why This Isn't Implemented Yet
1. Requires access to modify the RunPod endpoint code
2. Needs cloud storage credentials in RunPod environment
3. Would change the API response format

## For Users
Until the proper solution is implemented:
- Use smaller image sizes for larger batches
- Or generate images one at a time
- The 10MB limit is a RunPod infrastructure constraint, not our choice