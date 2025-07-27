FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /

# Install system dependencies (ignore NVIDIA repo errors)
RUN rm -f /etc/apt/sources.list.d/cuda* && \
    apt-get update || true && \
    apt-get install -y \
    git \
    python3-pip \
    wget \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI

WORKDIR /ComfyUI

# Install numpy first to ensure it's available
RUN pip install --no-cache-dir numpy==1.24.3

# Install ComfyUI requirements
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir -r requirements.txt

# Install additional requirements for RunPod and R2
RUN pip install --no-cache-dir runpod boto3 requests

# Install image processing packages that FLUX needs
# Force rebuild: 2025-07-27 - Added complete LoRA support
RUN pip install --no-cache-dir --force-reinstall numpy==1.24.3 pillow scipy

# Volume mount point - uses your existing volume
VOLUME ["/workspace"]

# Copy the FLUX handler and scripts
COPY src/flux_handler.py /handler.py
COPY src/workflows/flux_simple.json /workflows/flux_simple.json
COPY src/workflows/flux_checkpoint.json /workflows/flux_checkpoint.json
COPY src/workflows/flux_actual.json /workflows/flux_actual.json
COPY src/workflows/flux_img2img.json /workflows/flux_img2img.json
COPY src/workflows/flux_with_lora.json /workflows/flux_with_lora.json
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Set environment variables
ENV PYTHONPATH=/ComfyUI:$PYTHONPATH
ENV COMFYUI_PATH=/ComfyUI
ENV PYTHONUNBUFFERED=1

# Run the startup script - check volume first, fallback to default
CMD ["/bin/bash", "-c", "if [ -f /workspace/start_volume.sh ]; then /workspace/start_volume.sh; else /start.sh; fi"]