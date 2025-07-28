#!/bin/bash
# Quick build script for LoRA update

echo "🚀 Building FLUX with LoRA support..."

# First, let's check if we have a working base image
if docker pull runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04; then
    echo "✅ Base image pulled successfully"
else
    echo "❌ Failed to pull base image"
    exit 1
fi

# Build with platform specification to avoid ARM/AMD mismatch
docker build --platform linux/amd64 -f Dockerfile.flux -t jpjpkimjp/flux-comfyui:lora-v1 . || {
    echo "❌ Build failed. Trying alternative approach..."
    
    # If main build fails, try a simpler approach
    echo "Creating temporary Dockerfile..."
    cat > Dockerfile.flux-temp << 'EOF'
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /

# Skip problematic apt-get and use pip only
RUN pip install --no-cache-dir git+https://github.com/comfyanonymous/ComfyUI.git
RUN pip install --no-cache-dir runpod boto3 requests numpy==1.24.3 pillow scipy

# Copy handler and workflows
COPY src/flux_handler.py /handler.py
COPY src/workflows/*.json /workflows/
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONUNBUFFERED=1
CMD ["/bin/bash", "/start.sh"]
EOF

    docker build --platform linux/amd64 -f Dockerfile.flux-temp -t jpjpkimjp/flux-comfyui:lora-v1 .
}

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📤 Pushing to Docker Hub..."
    docker push jpjpkimjp/flux-comfyui:lora-v1
    
    echo ""
    echo "✅ Done! Update your RunPod endpoint to use:"
    echo "   jpjpkimjp/flux-comfyui:lora-v1"
else
    echo "❌ Build failed"
fi