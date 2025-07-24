FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    wget \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI

WORKDIR /ComfyUI

# Install ComfyUI requirements
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir -r requirements.txt

# Install additional requirements for RunPod and R2
RUN pip install runpod boto3 requests

# Volume mount point - uses your existing volume
VOLUME ["/workspace"]

# Copy the FLUX handler
COPY src/flux_handler.py /handler.py
COPY src/workflows/flux_simple.json /workflows/flux_simple.json

# Set environment variables
ENV PYTHONPATH=/ComfyUI:$PYTHONPATH
ENV COMFYUI_PATH=/ComfyUI
ENV PYTHONUNBUFFERED=1

# Create startup script to handle model linking
RUN echo '#!/bin/bash\n\
echo "Setting up model directories..."\n\
# Check where models actually are\n\
echo "Checking /workspace structure:"\n\
ls -la /workspace/ || echo "No /workspace"\n\
ls -la /workspace/ComfyUI/ || echo "No /workspace/ComfyUI"\n\
ls -la /workspace/ComfyUI/models/ || echo "No /workspace/ComfyUI/models"\n\
# Try different mount points\n\
if [ -d "/workspace/ComfyUI/models" ]; then\n\
    echo "Found models at /workspace/ComfyUI/models"\n\
    rm -rf /ComfyUI/models\n\
    ln -s /workspace/ComfyUI/models /ComfyUI/models\n\
elif [ -d "/runpod-volume/ComfyUI/models" ]; then\n\
    echo "Found models at /runpod-volume/ComfyUI/models"\n\
    rm -rf /ComfyUI/models\n\
    ln -s /runpod-volume/ComfyUI/models /ComfyUI/models\n\
else\n\
    echo "WARNING: No models directory found!"\n\
    echo "Searched: /workspace/ComfyUI/models and /runpod-volume/ComfyUI/models"\n\
fi\n\
# List what we have\n\
echo "ComfyUI models directory contents:"\n\
ls -la /ComfyUI/models/ || echo "Failed to list /ComfyUI/models"\n\
# Start the handler\n\
python3 -u /handler.py' > /start.sh && chmod +x /start.sh

# Run the startup script
CMD ["/start.sh"]