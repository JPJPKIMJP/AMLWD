#!/bin/bash

# Build and deploy FLUX Docker to RunPod - Version 2 with better logging

echo "Building FLUX Docker image v2..."

# Build the Docker image with new tag
docker build -f Dockerfile.flux -t flux-comfyui:v2 .

# Tag for your Docker registry (replace with your registry)
# docker tag flux-comfyui:v2 your-registry/flux-comfyui:v2
# docker push your-registry/flux-comfyui:v2

echo "Docker image built successfully!"
echo ""
echo "To deploy to RunPod:"
echo "1. Push this image to a Docker registry (Docker Hub, etc.)"
echo "2. In RunPod:"
echo "   - Edit your endpoint"
echo "   - Update the Docker image to use :v2 tag"
echo "   - Set Max Workers to 0, save, then back to 2"
echo ""
echo "This version includes:"
echo "- RunPod logger for better debugging"
echo "- Unbuffered Python output"
echo "- Better error handling and logging"