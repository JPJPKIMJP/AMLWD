#!/bin/bash

# Build and deploy FLUX Docker to RunPod - Version 3 with model path fixes

echo "Building FLUX Docker image v3..."

# Build the Docker image with new tag
docker build -f Dockerfile.flux -t flux-comfyui:v3 .

# Tag for your Docker registry (replace with your registry)
# docker tag flux-comfyui:v3 your-registry/flux-comfyui:v3
# docker push your-registry/flux-comfyui:v3

echo "Docker image built successfully!"
echo ""
echo "IMPORTANT: Model Setup Instructions"
echo "==================================="
echo ""
echo "The error shows no models are found. Your RunPod volume needs FLUX models in:"
echo "  /workspace/ComfyUI/models/"
echo ""
echo "Required directory structure:"
echo "  /workspace/ComfyUI/models/checkpoints/  (for .safetensors checkpoint files)"
echo "  /workspace/ComfyUI/models/vae/          (for VAE models like ae.sft)"
echo "  /workspace/ComfyUI/models/unet/         (for UNET models)"
echo "  /workspace/ComfyUI/models/clip/         (for CLIP models)"
echo ""
echo "You can either:"
echo "1. Upload FLUX checkpoint to /workspace/ComfyUI/models/checkpoints/"
echo "2. Or upload individual models to their respective folders"
echo ""
echo "To deploy:"
echo "1. Push this image to Docker registry with :v3 tag"
echo "2. Update RunPod endpoint to use :v3"
echo "3. Set Max Workers to 0, save, then back to 2"