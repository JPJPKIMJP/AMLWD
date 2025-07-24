#!/bin/bash

echo "=== Checking RunPod Volume Model Structure ==="
echo ""

# Check if we're in regular pod or serverless
echo "Checking mount points:"
ls -la /workspace >/dev/null 2>&1 && echo "✓ /workspace exists" || echo "✗ /workspace not found"
ls -la /runpod-volume >/dev/null 2>&1 && echo "✓ /runpod-volume exists" || echo "✗ /runpod-volume not found"
echo ""

# Set the base path
if [ -d "/workspace/ComfyUI" ]; then
    BASE="/workspace/ComfyUI"
elif [ -d "/runpod-volume/ComfyUI" ]; then
    BASE="/runpod-volume/ComfyUI"
else
    echo "ERROR: No ComfyUI directory found!"
    exit 1
fi

echo "Using base path: $BASE"
echo ""

# Check each model directory
echo "=== CHECKPOINTS ==="
echo "Path: $BASE/models/checkpoints/"
ls -la "$BASE/models/checkpoints/" 2>/dev/null | grep -E '\.(safetensors|ckpt|pt)$' || echo "No checkpoint files found"
echo ""

echo "=== UNET MODELS ==="
echo "Path: $BASE/models/unet/"
ls -la "$BASE/models/unet/" 2>/dev/null | grep -E '\.(safetensors|ckpt|pt)$' || echo "No UNET files found"
echo ""

echo "=== VAE MODELS ==="
echo "Path: $BASE/models/vae/"
ls -la "$BASE/models/vae/" 2>/dev/null | grep -E '\.(safetensors|ckpt|pt|sft)$' || echo "No VAE files found"
echo ""

echo "=== CLIP MODELS ==="
echo "Path: $BASE/models/clip/"
ls -la "$BASE/models/clip/" 2>/dev/null | grep -E '\.(safetensors|ckpt|pt|bin)$' || echo "No CLIP files found"
echo ""

echo "=== LORA MODELS ==="
echo "Path: $BASE/models/loras/"
ls -la "$BASE/models/loras/" 2>/dev/null | grep -E '\.(safetensors|ckpt|pt)$' || echo "No LoRA files found"
echo ""

# Also check for FLUX-specific directories
echo "=== CHECKING FLUX-SPECIFIC PATHS ==="
find "$BASE/models" -name "*flux*" -type f 2>/dev/null | head -20
echo ""

# Summary
echo "=== SUMMARY ==="
echo "Total model files by type:"
echo -n "Checkpoints: "; find "$BASE/models/checkpoints" -name "*.safetensors" -o -name "*.ckpt" 2>/dev/null | wc -l
echo -n "UNET: "; find "$BASE/models/unet" -name "*.safetensors" -o -name "*.ckpt" 2>/dev/null | wc -l
echo -n "VAE: "; find "$BASE/models/vae" -name "*.safetensors" -o -name "*.ckpt" -o -name "*.sft" 2>/dev/null | wc -l
echo -n "CLIP: "; find "$BASE/models/clip" -name "*.safetensors" -o -name "*.bin" 2>/dev/null | wc -l