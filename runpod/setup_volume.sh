#!/bin/bash
# Setup script for RunPod Network Volume with ComfyUI models

VOLUME_PATH="/workspace/ComfyUI/models"

echo "Setting up ComfyUI models volume..."

# Create directory structure
mkdir -p $VOLUME_PATH/{checkpoints,loras,vae,controlnet,upscale_models,embeddings,clip_vision}

# Download essential models
cd $VOLUME_PATH/checkpoints

# SD 1.5 Base Model (~4GB)
if [ ! -f "sd_v1-5.safetensors" ]; then
    echo "Downloading SD 1.5..."
    wget -c https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors \
         -O sd_v1-5.safetensors
fi

# Popular community model - RealisticVision (~2GB)
if [ ! -f "realisticVision_v5.safetensors" ]; then
    echo "Downloading RealisticVision v5..."
    wget -c https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/Realistic_Vision_V5.1.safetensors \
         -O realisticVision_v5.safetensors
fi

# VAE
cd $VOLUME_PATH/vae
if [ ! -f "vae-ft-mse-840000-ema-pruned.safetensors" ]; then
    echo "Downloading VAE..."
    wget -c https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors
fi

# Upscaler
cd $VOLUME_PATH/upscale_models
if [ ! -f "RealESRGAN_x4plus.pth" ]; then
    echo "Downloading RealESRGAN..."
    wget -c https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
fi

# Popular embeddings
cd $VOLUME_PATH/embeddings
if [ ! -f "EasyNegative.safetensors" ]; then
    echo "Downloading EasyNegative..."
    wget -c https://huggingface.co/datasets/gsdf/EasyNegative/resolve/main/EasyNegative.safetensors
fi

echo "Basic setup complete!"
echo "Volume contains:"
du -sh $VOLUME_PATH/*

echo ""
echo "To add LoRAs:"
echo "1. Download from Civitai to your computer"
echo "2. Upload to $VOLUME_PATH/loras/"
echo ""
echo "Your models will persist across container restarts!"