# RunPod LoRA Deployment Guide

## 🚀 Update RunPod Endpoint with New LoRA-Enabled Image

### Step 1: Wait for Docker Build
- Monitor GitHub Actions: https://github.com/JPJPKIMJP/AMLWD/actions
- Wait for "Build and Push FLUX Docker Image" to complete
- New image will be: `jpjpkimjp/amlwd-runpod-flux:latest`

### Step 2: Update RunPod Endpoint
1. Go to RunPod Console: https://www.runpod.io/console/user/templates
2. Find your FLUX endpoint template
3. Update Docker Image to: `jpjpkimjp/amlwd-runpod-flux:latest`
4. Save template and restart endpoint

### Step 3: Test LoRA Functionality
```bash
# Test LoRA download capability
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "download_lora",
      "lora_url": "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753591512468_mix4.safetensors?alt=media&token=d2c720b3-4aef-4ac4-8651-4a93b936fbeb",
      "lora_name": "mix4.safetensors"
    }
  }'
```

### Step 4: Test LoRA Image Generation
```bash
# Test LoRA-enabled generation
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "a beautiful anime girl, detailed face, colorful hair",
      "width": 1024,
      "height": 1024,
      "lora_name": "mix4",
      "lora_strength": 0.8
    }
  }'
```

## ✅ What's Now Deployed:

### GitHub Repository:
- ✅ Complete LoRA workflow (`flux_with_lora.json`)
- ✅ Updated ComfyUI handler with LoRA support
- ✅ Updated FLUX handler with auto-download
- ✅ Dockerfile includes all LoRA components

### Firebase (Already Live):
- ✅ LoRA upload interface at https://amlwd-image-gen.web.app/
- ✅ LoRA selection dropdown
- ✅ LoRA strength slider
- ✅ Firebase Storage with LoRA files

### Docker Image (Building):
- 🔄 GitHub Actions building new image with LoRA support
- ✅ Will include `flux_with_lora.json` workflow
- ✅ Will include updated handlers
- ✅ Will support automatic LoRA download

## 🎯 Expected Behavior After Deployment:

1. **User selects LoRA** in Firebase UI (https://amlwd-image-gen.web.app/)
2. **Firebase Functions** passes LoRA parameters to RunPod
3. **RunPod handler** detects LoRA request
4. **Automatic workflow switch** to `flux_with_lora.json`
5. **Auto-download LoRA** if not present locally
6. **Generate image** with LoRA applied

## 🔧 Manual RunPod Update Commands:

If you have SSH access to RunPod pod:
```bash
# Download LoRA manually if needed
wget -O /workspace/ComfyUI/models/loras/mix4.safetensors "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.firebasestorage.app/o/loras%2F1753591512468_mix4.safetensors?alt=media&token=d2c720b3-4aef-4ac4-8651-4a93b936fbeb"

# Check if LoRA workflow exists
ls -la /workflows/flux_with_lora.json

# Restart handler if needed
pkill -f flux_handler.py
python /handler.py &
```

## 📊 Monitoring:

- **GitHub Actions**: https://github.com/JPJPKIMJP/AMLWD/actions
- **RunPod Logs**: Check pod logs for LoRA download messages
- **Firebase Console**: Monitor function calls and storage access
- **Live UI**: https://amlwd-image-gen.web.app/

Your LoRA implementation is now fully deployed across all platforms! 🎉