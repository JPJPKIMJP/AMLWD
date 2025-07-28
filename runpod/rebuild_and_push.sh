#!/bin/bash
# Rebuild and push Docker image with LoRA download support

echo "🔨 Rebuilding Docker image with LoRA download support..."

# Build the image
docker build -t flux-comfyui-lora:latest .

# Tag for Docker Hub (replace YOUR_DOCKERHUB_USERNAME with your actual username)
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-YOUR_DOCKERHUB_USERNAME}"
docker tag flux-comfyui-lora:latest $DOCKERHUB_USERNAME/flux-comfyui:latest

echo "📤 Pushing to Docker Hub..."
docker push $DOCKERHUB_USERNAME/flux-comfyui:latest

echo "✅ Done! Update your RunPod endpoint with the new image."
echo ""
echo "Then run the LoRA deployment with:"
echo "export RUNPOD_API_KEY='your-new-api-key'"
echo "export RUNPOD_ENDPOINT_ID='your-endpoint-id'"
echo "python3 ../firebase/quick_deploy_lora.py"