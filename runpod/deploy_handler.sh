#!/bin/bash

# Deploy updated flux_handler.py to RunPod

echo "Deploying updated flux_handler.py to RunPod..."

# Build and push the Docker image
cd /Users/jpsmac/AMLWD/runpod

# Ensure workflows directory exists in src
if [ ! -d "src/workflows" ]; then
    echo "Error: src/workflows directory not found!"
    exit 1
fi

# Check that critical workflow files exist
if [ ! -f "src/workflows/flux_actual.json" ] || [ ! -f "src/workflows/flux_with_lora.json" ]; then
    echo "Error: Required workflow files not found!"
    exit 1
fi

echo "Found workflow files:"
ls -la src/workflows/flux*.json

# Build the image
echo "\nBuilding Docker image..."
docker build -t jpjpkimjp/flux-comfyui:latest .

# Check if build succeeded
if [ $? -ne 0 ]; then
    echo "Docker build failed!"
    exit 1
fi

# Push to Docker Hub
echo "\nPushing to Docker Hub..."
docker push jpjpkimjp/flux-comfyui:latest

echo "Docker image pushed successfully!"
echo "The RunPod serverless endpoint will automatically use the updated image on next job."
echo ""
echo "To test LoRA functionality:"
echo "1. Go to https://amlwd-image-gen.web.app/"
echo "2. Select a LoRA (e.g., mix4)"
echo "3. Generate an image"
echo "4. Check RunPod logs to verify LoRA is being loaded"