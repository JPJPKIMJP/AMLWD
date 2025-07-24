# ComfyUI Models Volume Structure

## Directory Layout
```
/workspace/ComfyUI/models/
├── checkpoints/          # Main model files
│   ├── sd_v1-5.safetensors                    # ~4GB
│   ├── dreamshaper_v8.safetensors             # ~2GB
│   ├── realisticVision_v5.safetensors         # ~2GB
│   └── sdxl_base_1.0.safetensors              # ~6.5GB
│
├── loras/               # LoRA files  
│   ├── anime_style.safetensors                # ~144MB
│   ├── detailed_eyes.safetensors              # ~144MB
│   ├── pixel_art.safetensors                  # ~144MB
│   └── realistic_skin.safetensors             # ~144MB
│
├── vae/                 # VAE files
│   ├── vae-ft-mse-840000-ema-pruned.safetensors  # ~335MB
│   └── sdxl_vae.safetensors                      # ~335MB
│
├── controlnet/          # ControlNet models
│   ├── control_v11p_sd15_openpose.safetensors    # ~1.5GB
│   ├── control_v11p_sd15_canny.safetensors       # ~1.5GB
│   └── control_v11f1p_sd15_depth.safetensors     # ~1.5GB
│
├── upscale_models/      # Upscalers
│   ├── RealESRGAN_x4plus.pth                     # ~64MB
│   └── 4x-UltraSharp.pth                         # ~64MB
│
├── embeddings/          # Textual inversions
│   ├── easynegative.pt                           # ~50KB
│   └── bad-hands-5.pt                            # ~50KB
│
└── clip_vision/         # For IPAdapter
    └── SD1.5/
        └── model.safetensors                      # ~1GB
```

## Essential Models to Start

### Minimum Setup (~6GB)
- `sd_v1-5.safetensors` - Base SD 1.5 model
- `vae-ft-mse-840000-ema-pruned.safetensors` - Better VAE
- 2-3 LoRAs of your choice

### Standard Setup (~20GB)
- 2-3 checkpoint models (SD 1.5 variants)
- 5-10 LoRAs
- 1-2 ControlNet models
- VAE and upscaler

### Full Setup (~50GB+)
- Multiple SD 1.5 and SDXL checkpoints
- 20+ LoRAs
- All ControlNet models
- IPAdapter models
- Multiple upscalers

## Where to Get Models

### Checkpoints (Base Models)
- **HuggingFace**: https://huggingface.co/models?other=stable-diffusion
- **Civitai**: https://civitai.com/models (community models)
- **Official**: 
  - SD 1.5: https://huggingface.co/runwayml/stable-diffusion-v1-5
  - SDXL: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0

### LoRAs
- **Civitai**: Best source for style/character LoRAs
- **HuggingFace**: More technical/research LoRAs

### ControlNet
- **HuggingFace lllyasviel**: https://huggingface.co/lllyasviel/ControlNet-v1-1

## Download Script Example
```bash
#!/bin/bash
# download_models.sh - Run this to populate your volume

MODELS_DIR="/workspace/ComfyUI/models"

# Create directories
mkdir -p $MODELS_DIR/{checkpoints,loras,vae,controlnet,upscale_models,embeddings}

# Download base SD 1.5
wget -O $MODELS_DIR/checkpoints/sd_v1-5.safetensors \
  https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors

# Download VAE
wget -O $MODELS_DIR/vae/vae-ft-mse-840000-ema-pruned.safetensors \
  https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors

# Download popular LoRA (example)
# Note: Civitai requires API token for direct downloads
# You might need to download manually and upload

echo "Base models downloaded!"
```