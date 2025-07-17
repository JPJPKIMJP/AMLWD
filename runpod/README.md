# RunPod Serverless Setup Guide

## Quick Setup Steps

### 1. Create RunPod Account
- Go to [RunPod.io](https://runpod.io)
- Sign up and add credits to your account

### 2. Create Serverless Endpoint

1. Go to **Serverless** → **Endpoints**
2. Click **New Endpoint**
3. Configure:
   - **Endpoint Name**: `amlwd-image-generator`
   - **Select Template**: Choose "Stable Diffusion" or "Custom"
   - **Container Image**: `runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04`
   - **Container Disk**: 20 GB
   - **Volume Disk**: 0 GB (unless you need persistent storage)

### 3. Deploy Using RunPod CLI

```bash
# Install RunPod CLI
pip install runpodctl

# Login
runpodctl login

# Deploy from this directory
cd runpod
runpodctl deploy --name amlwd-image-generator
```

### 4. Deploy Using Web Interface

1. In RunPod dashboard, go to your endpoint
2. Click **Deploy New Version**
3. Upload this folder as a zip file OR
4. Use Docker Hub:
   ```bash
   # Build and push to Docker Hub
   docker build -t your-username/amlwd-runpod:latest .
   docker push your-username/amlwd-runpod:latest
   ```

### 5. Get Your Credentials

After deployment:
1. Go to your endpoint in RunPod dashboard
2. Copy:
   - **Endpoint ID**: (looks like `xxxxxx`)
   - **API Key**: Settings → API Keys → Create new key

### 6. Configure Backend

Create a `.env` file in the backend directory:
```env
RUNPOD_API_KEY=your_api_key_here
RUNPOD_ENDPOINT_ID=your_endpoint_id_here
```

### 7. Test the Endpoint

```bash
# Test with curl
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "a beautiful sunset",
      "width": 512,
      "height": 512
    }
  }'
```

## Cost Estimates

- **Idle Time**: ~$0.00025/second when no requests
- **Active Time**: ~$0.0011/second during generation
- **Average Cost**: ~$0.02-0.05 per image

## Optimization Tips

1. Set **Max Workers** to control costs
2. Use **Active Workers** for faster response
3. Set **Idle Timeout** to 5-10 seconds
4. Enable **Flash Boot** for faster cold starts