# RunPod Handler Update Instructions

The RunPod handler has been updated to support custom LoRA downloads from Firebase Storage URLs!

## Quick Update (Without Docker Rebuild)

1. **SSH into your RunPod instance**:
   ```bash
   ssh root@[YOUR_RUNPOD_IP] -p [YOUR_SSH_PORT]
   ```

2. **Download and run the update script**:
   ```bash
   wget https://raw.githubusercontent.com/JPJPKIMJP/AMLWD/main/runpod/update_handler.sh
   chmod +x update_handler.sh
   ./update_handler.sh
   ```

3. **That's it!** The handler will automatically use the updated code for the next image generation.

## What's New

- **Automatic LoRA Download**: When a `lora_url` is provided, the handler downloads it from Firebase Storage
- **Smart Caching**: Downloaded LoRAs are cached, so they don't need to be downloaded again
- **Multiple Storage Locations**: Tries multiple paths to find a writable location for LoRAs
- **Error Handling**: Proper error messages if download fails

## How It Works

1. Frontend sends: `lora_name: "my_lora"` and `lora_url: "https://firebasestorage.googleapis.com/..."`
2. Handler checks if LoRA already exists locally
3. If not, downloads it from the URL to `/workspace/ComfyUI/models/loras/`
4. Updates the workflow to use the downloaded LoRA
5. Generates the image with the custom style!

## Testing

Test with a custom LoRA:
```json
{
  "input": {
    "prompt": "a beautiful portrait",
    "lora_name": "my_custom_lora",
    "lora_url": "https://firebasestorage.googleapis.com/...",
    "lora_strength": 0.8
  }
}
```

## Troubleshooting

- **Permission Errors**: The handler tries multiple paths. At least one should be writable.
- **Download Failures**: Check that the Firebase Storage URL is publicly accessible
- **LoRA Not Applied**: Ensure the LoRA is FLUX-compatible (not SD1.5)

## Full Rebuild (Optional)

If you prefer to rebuild the Docker image:
```bash
cd /path/to/AMLWD/runpod
./deploy_flux_v4.sh
```

But this is NOT necessary - the quick update method above is sufficient!