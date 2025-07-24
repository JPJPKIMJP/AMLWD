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

# Start the handler
exec python3 -u /handler.py