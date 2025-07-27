# RunPod Deployment Instructions

Since Docker is not available on this system, here are the manual steps to deploy the updated handler with LoRA support.

## Option 1: Quick Update (Recommended - No Docker Required!)

This is the easiest way to update your RunPod endpoint with the new LoRA functionality:

1. **SSH into your RunPod instance**:
   ```bash
   ssh root@[YOUR_RUNPOD_IP] -p [YOUR_SSH_PORT]
   ```

2. **Run the update command**:
   ```bash
   wget https://raw.githubusercontent.com/JPJPKIMJP/AMLWD/main/runpod/update_handler.sh && \
   chmod +x update_handler.sh && \
   ./update_handler.sh
   ```

3. **That's it!** Your endpoint now supports custom LoRA downloads.

## Option 2: Full Docker Rebuild (Requires Docker)

If you want to rebuild the Docker image:

1. **On a machine with Docker installed**, clone the repo:
   ```bash
   git clone https://github.com/JPJPKIMJP/AMLWD.git
   cd AMLWD/runpod
   ```

2. **Run the deployment script**:
   ```bash
   ./deploy_flux_complete.sh
   ```

3. **Update RunPod endpoint**:
   - Go to RunPod Dashboard
   - Click on your endpoint
   - Click "Manage" → "Edit Endpoint"
   - Update Docker image to: `jpjpkimjp/flux-comfyui:lora-v1`
   - Set Max Workers to 0, Save
   - Wait 30 seconds
   - Set Max Workers back to 2, Save

## Testing the New LoRA Feature

Once updated, test with this payload:

```json
{
  "input": {
    "prompt": "a beautiful portrait in anime style",
    "width": 1024,
    "height": 1024,
    "lora_name": "my_custom_lora",
    "lora_url": "https://firebasestorage.googleapis.com/v0/b/amlwd-image-gen.appspot.com/o/loras%2FyourUserId%2Fyour_lora.safetensors?alt=media&token=xxx",
    "lora_strength": 0.8
  }
}
```

## What's New

✅ **Automatic LoRA Downloads**: Downloads LoRAs from Firebase Storage URLs  
✅ **Smart Caching**: Downloaded once, reused for future generations  
✅ **Multiple Path Support**: Tries different locations to ensure success  
✅ **Error Handling**: Clear error messages if something goes wrong  

## Troubleshooting

**LoRA not downloading?**
- Check that the Firebase URL is publicly accessible
- Ensure the LoRA filename ends with `.safetensors`
- Check RunPod logs for download errors

**LoRA not applying?**
- Verify the LoRA is FLUX-compatible (not SD1.5)
- Check that the LoRA node exists in the workflow
- Try with a lower strength value (0.5-0.8)

## Success Confirmation

After updating, you should see in the RunPod logs:
```
Using custom LoRA from URL: https://...
Downloading custom LoRA: my_lora.safetensors
Successfully downloaded my_lora.safetensors to /workspace/ComfyUI/models/loras/my_lora.safetensors (25.3 MB)
```

---

**Choose Option 1 (Quick Update) if you just want to get the LoRA feature working quickly!**