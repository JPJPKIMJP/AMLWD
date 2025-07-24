#!/bin/bash
echo "Starting FLUX handler..."
echo "Setting up model directories..."

# Check where models actually are
echo "Checking /workspace structure:"
ls -la /workspace/ 2>/dev/null || echo "No /workspace"
ls -la /workspace/ComfyUI/ 2>/dev/null || echo "No /workspace/ComfyUI"
ls -la /workspace/ComfyUI/models/ 2>/dev/null || echo "No /workspace/ComfyUI/models"

echo "Checking /runpod-volume structure:"
ls -la /runpod-volume/ 2>/dev/null || echo "No /runpod-volume"

# Try different mount points
if [ -d "/workspace/ComfyUI/models" ]; then
    echo "Found models at /workspace/ComfyUI/models"
    rm -rf /ComfyUI/models
    ln -s /workspace/ComfyUI/models /ComfyUI/models
    
    # Create symlinks for text encoders in clip directory if needed
    if [ -d "/workspace/ComfyUI/models/text_encoders" ] && [ -d "/ComfyUI/models/clip" ]; then
        echo "Linking text encoders to clip directory..."
        ln -sf /workspace/ComfyUI/models/text_encoders/*.safetensors /ComfyUI/models/clip/ 2>/dev/null || true
    fi
elif [ -d "/runpod-volume/ComfyUI/models" ]; then
    echo "Found models at /runpod-volume/ComfyUI/models"
    rm -rf /ComfyUI/models
    ln -s /runpod-volume/ComfyUI/models /ComfyUI/models
    
    # Create symlinks for text encoders in clip directory if needed
    if [ -d "/runpod-volume/ComfyUI/models/text_encoders" ] && [ -d "/ComfyUI/models/clip" ]; then
        echo "Linking text encoders to clip directory..."
        ln -sf /runpod-volume/ComfyUI/models/text_encoders/*.safetensors /ComfyUI/models/clip/ 2>/dev/null || true
    fi
else
    echo "WARNING: No models directory found!"
    echo "Searched: /workspace/ComfyUI/models and /runpod-volume/ComfyUI/models"
fi

# List what we have
echo "ComfyUI models directory contents:"
ls -la /ComfyUI/models/ 2>/dev/null || echo "Failed to list /ComfyUI/models"

# Create diffusion_models directory if it doesn't exist
mkdir -p /ComfyUI/models/diffusion_models

# Link diffusion models if they exist in the volume
if [ -d "/runpod-volume/ComfyUI/models/diffusion_models" ]; then
    echo "Linking diffusion models from volume..."
    ln -sf /runpod-volume/ComfyUI/models/diffusion_models/* /ComfyUI/models/diffusion_models/ 2>/dev/null || true
fi

# Check for FLUX model in various locations and link if needed
echo "Searching for FLUX model..."
FLUX_MODEL="flux1-dev-kontext_fp8_scaled.safetensors"

if [ -f "/ComfyUI/models/diffusion_models/${FLUX_MODEL}" ]; then
    echo "✓ FLUX model found in diffusion_models"
elif [ -f "/ComfyUI/models/checkpoints/${FLUX_MODEL}" ]; then
    echo "FLUX model found in checkpoints, linking to diffusion_models..."
    ln -sf "/ComfyUI/models/checkpoints/${FLUX_MODEL}" "/ComfyUI/models/diffusion_models/"
    echo "✓ Linked FLUX model to diffusion_models"
elif [ -f "/ComfyUI/models/unet/${FLUX_MODEL}" ]; then
    echo "FLUX model found in unet, linking to diffusion_models..."
    ln -sf "/ComfyUI/models/unet/${FLUX_MODEL}" "/ComfyUI/models/diffusion_models/"
    echo "✓ Linked FLUX model to diffusion_models"
elif [ -f "/runpod-volume/ComfyUI/models/checkpoints/${FLUX_MODEL}" ]; then
    echo "FLUX model found in volume checkpoints, linking..."
    ln -sf "/runpod-volume/ComfyUI/models/checkpoints/${FLUX_MODEL}" "/ComfyUI/models/diffusion_models/"
    echo "✓ Linked FLUX model from volume"
else
    echo "ERROR: FLUX model '${FLUX_MODEL}' not found in any location!"
    echo "Searched:"
    echo "  - /ComfyUI/models/diffusion_models/"
    echo "  - /ComfyUI/models/checkpoints/"
    echo "  - /ComfyUI/models/unet/"
    echo "  - /runpod-volume/ComfyUI/models/checkpoints/"
fi

# List final model directories for debugging
echo "Final model directory contents:"
echo "Diffusion models:"
ls -la /ComfyUI/models/diffusion_models/ 2>/dev/null || echo "No diffusion_models directory"
echo "CLIP models:"
ls -la /ComfyUI/models/clip/ 2>/dev/null | head -5
echo "VAE models:"
ls -la /ComfyUI/models/vae/ 2>/dev/null | head -5

# Start the handler
exec python3 -u /handler.py