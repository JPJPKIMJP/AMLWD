# Fix FLUX Model Path in RunPod Serverless

## Problem
The FLUX model `flux1-dev-kontext_fp8_scaled.safetensors` cannot be found in serverless environment at:
- `/runpod-volume/ComfyUI/models/diffusion_models/`
- `/runpod-volume/ComfyUI/models/unet/`

Other models (VAE, CLIP) are found successfully, indicating the volume is mounted correctly.

## Solution Steps

### 1. Start a Regular RunPod Pod
```bash
# Start a pod with your network volume attached
# Use the same template as your serverless endpoint but in pod mode
```

### 2. Check Current Model Location
Once in the pod, run these commands:

```bash
# Find the FLUX model
find /workspace -name "*flux*" -type f 2>/dev/null | grep -E "\.(safetensors|ckpt|pt)$"

# Check common locations
ls -la /workspace/ComfyUI/models/checkpoints/
ls -la /workspace/ComfyUI/models/unet/
ls -la /workspace/ComfyUI/models/diffusion_models/

# Check if diffusion_models directory exists
ls -la /workspace/ComfyUI/models/
```

### 3. Create diffusion_models Directory and Copy Model
```bash
# Create the directory if it doesn't exist
mkdir -p /workspace/ComfyUI/models/diffusion_models/

# Copy the FLUX model to the correct location
# Replace SOURCE_PATH with where you found the model
cp /workspace/ComfyUI/models/checkpoints/flux1-dev-kontext_fp8_scaled.safetensors \
   /workspace/ComfyUI/models/diffusion_models/

# Verify it's there
ls -la /workspace/ComfyUI/models/diffusion_models/
```

### 4. Update start.sh to Handle Both Locations
Update the start.sh to check multiple locations for the FLUX model:

```bash
# After linking models directory, check for FLUX model
echo "Checking for FLUX model..."
if [ -f "/ComfyUI/models/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors" ]; then
    echo "FLUX model found in diffusion_models"
elif [ -f "/ComfyUI/models/checkpoints/flux1-dev-kontext_fp8_scaled.safetensors" ]; then
    echo "FLUX model found in checkpoints, linking to diffusion_models..."
    mkdir -p /ComfyUI/models/diffusion_models
    ln -sf /ComfyUI/models/checkpoints/flux1-dev-kontext_fp8_scaled.safetensors \
           /ComfyUI/models/diffusion_models/
elif [ -f "/ComfyUI/models/unet/flux1-dev-kontext_fp8_scaled.safetensors" ]; then
    echo "FLUX model found in unet, linking to diffusion_models..."
    mkdir -p /ComfyUI/models/diffusion_models
    ln -sf /ComfyUI/models/unet/flux1-dev-kontext_fp8_scaled.safetensors \
           /ComfyUI/models/diffusion_models/
else
    echo "WARNING: FLUX model not found!"
fi
```

### 5. Alternative: Update Workflow to Use checkpoints
If the model is in checkpoints directory, update the workflow:

```json
"37": {
  "inputs": {
    "ckpt_name": "flux1-dev-kontext_fp8_scaled.safetensors"
  },
  "class_type": "CheckpointLoaderSimple",
  "_meta": {
    "title": "Load Checkpoint"
  }
}
```

Instead of:
```json
"37": {
  "inputs": {
    "unet_name": "flux1-dev-kontext_fp8_scaled.safetensors",
    "weight_dtype": "default"
  },
  "class_type": "UNETLoader"
}
```

### 6. Verify Volume Persistence
After copying the model, stop and restart the pod to ensure changes persist:
```bash
# In a new pod
ls -la /workspace/ComfyUI/models/diffusion_models/
# Should show your FLUX model
```

### 7. Test Serverless Again
After ensuring the model is in the correct location, test your serverless endpoint again.