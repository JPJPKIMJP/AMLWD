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

# Create symlink to use existing models
RUN ln -s /workspace/ComfyUI/models /ComfyUI/models

# Copy the FLUX handler
COPY src/flux_handler.py /handler.py
COPY src/workflows/flux_simple.json /workflows/flux_simple.json

# Set environment variables
ENV PYTHONPATH=/ComfyUI:$PYTHONPATH
ENV COMFYUI_PATH=/ComfyUI

# Run the handler
CMD ["python", "-u", "/handler.py"]