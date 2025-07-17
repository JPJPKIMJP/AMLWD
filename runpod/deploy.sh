#!/bin/bash

# RunPod Deployment Script

echo "🚀 AMLWD RunPod Deployment"
echo "=========================="
echo ""

# Check if runpodctl is installed
if ! command -v runpodctl &> /dev/null; then
    echo "❌ runpodctl not found. Installing..."
    pip install runpodctl
fi

# Check for environment variables
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Please enter your RunPod API Key:"
    read -s RUNPOD_API_KEY
    export RUNPOD_API_KEY
fi

# Create deployment configuration
cat > runpod.toml << EOF
[project]
name = "amlwd-image-generator"
base_image = "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"

[project.env]
MODEL_ID = "runwayml/stable-diffusion-v1-5"

[deployment]
min_workers = 0
max_workers = 3
idle_timeout = 10
flash_boot = true
gpu_type = "AMPERE_16"
EOF

echo "📦 Building Docker image..."
docker build -t amlwd-runpod:latest .

echo ""
echo "🎯 Deployment Options:"
echo "1. Deploy using RunPod CLI (recommended)"
echo "2. Generate Docker commands for manual deployment"
echo "3. Exit"
echo ""
echo -n "Choose option (1-3): "
read choice

case $choice in
    1)
        echo "🚀 Deploying to RunPod..."
        runpodctl deploy
        ;;
    2)
        echo ""
        echo "📋 Manual deployment commands:"
        echo ""
        echo "# 1. Tag for Docker Hub:"
        echo "docker tag amlwd-runpod:latest YOUR_DOCKERHUB_USERNAME/amlwd-runpod:latest"
        echo ""
        echo "# 2. Push to Docker Hub:"
        echo "docker push YOUR_DOCKERHUB_USERNAME/amlwd-runpod:latest"
        echo ""
        echo "# 3. In RunPod dashboard, use this image:"
        echo "YOUR_DOCKERHUB_USERNAME/amlwd-runpod:latest"
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
esac

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Go to https://runpod.io/console/serverless"
echo "2. Find your endpoint and copy the Endpoint ID"
echo "3. Create .env file in backend/ directory with:"
echo "   RUNPOD_API_KEY=your_key_here"
echo "   RUNPOD_ENDPOINT_ID=your_endpoint_id_here"