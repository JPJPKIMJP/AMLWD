#!/bin/bash

# Build and deploy FLUX Docker to RunPod - Version 4 with serverless volume fix

echo "Building FLUX Docker image v4 (serverless volume fix)..."

# Build the Docker image with new tag
docker build -f Dockerfile.flux -t flux-comfyui:v4 .

# Tag for your Docker registry (replace with your registry)
# docker tag flux-comfyui:v4 your-registry/flux-comfyui:v4
# docker push your-registry/flux-comfyui:v4

echo "Docker image built successfully!"
echo ""
echo "Key Changes in v4:"
echo "=================="
echo "- Checks both /workspace and /runpod-volume mount points"
echo "- Better model detection and logging"
echo "- Runtime volume linking (not build-time)"
echo "- Support for both FLUX workflows"
echo ""
echo "To deploy:"
echo "1. Push image with :v4 tag to your registry"
echo "2. Update RunPod endpoint to use :v4"
echo "3. IMPORTANT: Set Max Workers to 0, save, wait, then back to 2"
echo ""
echo "Your models should be at one of these locations:"
echo "- /workspace/ComfyUI/models/ (regular pods)"
echo "- /runpod-volume/ComfyUI/models/ (serverless)"