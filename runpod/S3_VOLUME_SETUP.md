# RunPod S3 Volume Setup for LoRA Storage

## Overview
This guide explains how to configure your RunPod serverless endpoint to use S3-compatible storage for persistent LoRA storage.

## Environment Variables to Add

Add these environment variables to your RunPod serverless endpoint:

```bash
# S3 Volume Configuration (for LoRA storage)
S3_ENDPOINT=https://s3api-us-ks-2.runpod.io
S3_BUCKET=82elxnhs55
S3_ACCESS_KEY=user_2zH4PpHJhiBtUPAk4NUr6fhk3YG
S3_SECRET_KEY=<YOUR_SECRET_KEY>

# Existing R2 Configuration (for image output)
R2_ENDPOINT=<your_r2_endpoint>
R2_BUCKET=<your_r2_bucket>
R2_ACCESS_KEY_ID=<your_r2_access_key>
R2_SECRET_ACCESS_KEY=<your_r2_secret>
R2_PUBLIC_URL=<your_r2_public_url>
```

## How to Add Environment Variables in RunPod

1. Go to your RunPod dashboard
2. Navigate to your serverless endpoint
3. Click on "Edit Endpoint"
4. Scroll to "Environment Variables" section
5. Add each variable with its value
6. Save the endpoint

## What This Does

- **S3 Volume**: Used for persistent LoRA storage across pod restarts
- **R2**: Used for generated image storage and delivery

## LoRA Storage Behavior

With S3 configured:
1. When you upload a LoRA through the web UI, it will be stored in S3
2. When generating images, the handler will:
   - Check S3 first for the LoRA
   - Download to local workspace if needed
   - Use the LoRA for generation
3. LoRAs persist across pod restarts

Without S3 configured:
- LoRAs only stored in `/workspace/` (temporary)
- Lost when pod restarts

## Testing

After configuration:
1. Upload a LoRA through the web UI
2. Generate an image with that LoRA
3. Restart your pod
4. Try generating with the same LoRA again - it should work!

## S3 Bucket Structure

```
82elxnhs55/
└── models/
    └── loras/
        ├── korean_lora.safetensors
        ├── raw_photo_lora.safetensors
        └── ... (other LoRAs)
```

## Deployment

After adding environment variables:
1. The next deployment will automatically use the updated handler
2. No code changes needed - just set the environment variables
3. The handler will automatically detect S3 configuration

## Troubleshooting

- Check RunPod logs for S3 connection status
- Verify environment variables are set correctly
- Ensure S3 credentials have read/write permissions