#!/bin/bash
# Manual Docker Build Script
# Use this if GitHub Actions isn't set up yet

echo "🐳 Manual FLUX Docker Build"
echo "=========================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker Desktop from https://docker.com"
    exit 1
fi

# Check if logged in to Docker Hub
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo "📝 Please log in to Docker Hub:"
    docker login
fi

echo "Building FLUX Docker image with numpy fix..."

# Build the image
docker build -f runpod/Dockerfile.flux -t jpjpkimjp/flux-comfyui:latest runpod/

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    echo "Pushing to Docker Hub..."
    docker push jpjpkimjp/flux-comfyui:latest
    
    if [ $? -eq 0 ]; then
        echo "✅ Push successful!"
        echo ""
        echo "Next steps:"
        echo "1. Go to RunPod dashboard"
        echo "2. Scale workers to 0"
        echo "3. Wait 30 seconds"
        echo "4. Scale workers to 1"
        echo "5. Test image generation - numpy should work now!"
    else
        echo "❌ Push failed. Please check your Docker Hub credentials"
    fi
else
    echo "❌ Build failed"
fi