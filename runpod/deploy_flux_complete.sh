#!/bin/bash

# Complete FLUX deployment script with updated handler
# This builds and pushes the Docker image with the new LoRA download feature

set -e  # Exit on error

echo "🚀 FLUX Complete Deployment with LoRA Support"
echo "============================================"

# Configuration
DOCKER_IMAGE="jpjpkimjp/flux-comfyui"
VERSION="lora-v1"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo ""
echo "📦 Building Docker image with updated handler..."
echo "This includes the new LoRA download functionality!"
echo ""

# Build the Docker image
docker build -f Dockerfile.flux -t ${DOCKER_IMAGE}:${VERSION} .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Tag as latest
docker tag ${DOCKER_IMAGE}:${VERSION} ${DOCKER_IMAGE}:latest

echo ""
echo "📤 Pushing to Docker Hub..."
echo "You may need to login: docker login"
echo ""

# Push to Docker Hub
docker push ${DOCKER_IMAGE}:${VERSION}
docker push ${DOCKER_IMAGE}:latest

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment Complete!"
    echo "======================"
    echo ""
    echo "Docker image pushed: ${DOCKER_IMAGE}:${VERSION}"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Go to RunPod Dashboard"
    echo "2. Find your endpoint"
    echo "3. Click 'Manage' → 'Edit Endpoint'"
    echo "4. Update Docker image to: ${DOCKER_IMAGE}:${VERSION}"
    echo "5. Set Max Workers to 0, Save"
    echo "6. Wait 30 seconds"
    echo "7. Set Max Workers back to 2, Save"
    echo ""
    echo "✨ New Features:"
    echo "- Automatic LoRA download from Firebase URLs"
    echo "- Smart caching (downloads only once)"
    echo "- Support for custom uploaded LoRAs"
    echo ""
    echo "🧪 Test with:"
    echo '{"input": {"prompt": "test", "lora_name": "my_lora", "lora_url": "https://..."}}'
    echo ""
else
    echo "❌ Docker push failed. Please run: docker login"
    exit 1
fi