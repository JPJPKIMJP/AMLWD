#!/bin/bash

# Build and deploy FLUX Docker to RunPod

echo "Building FLUX Docker image..."

# Build the Docker image
docker build -f Dockerfile.flux -t flux-comfyui:latest .

# Tag for your Docker registry (replace with your registry)
# docker tag flux-comfyui:latest your-registry/flux-comfyui:latest
# docker push your-registry/flux-comfyui:latest

echo "Docker image built successfully!"
echo ""
echo "To deploy to RunPod:"
echo "1. Push this image to a Docker registry (Docker Hub, etc.)"
echo "2. In RunPod:"
echo "   - Create new endpoint"
echo "   - Select 'Custom Docker Image'"
echo "   - Enter your image URL"
echo "   - Attach your network volume to /workspace"
echo "   - Add R2 environment variables (optional)"
echo ""
echo "Environment variables to add in RunPod:"
echo "  R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com"
echo "  R2_ACCESS_KEY_ID=your_key"
echo "  R2_SECRET_ACCESS_KEY=your_secret"
echo "  R2_BUCKET=your_bucket"
echo "  R2_PUBLIC_URL=https://pub-xxx.r2.dev"