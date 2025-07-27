#!/bin/bash

echo "Cleaning up old incompatible LoRAs..."

# Remove the actual old LoRA files if they exist
LORA_DIRS=(
    "/workspace/ComfyUI/models/loras"
    "/ComfyUI/models/loras"
    "/runpod-volume/ComfyUI/models/loras"
)

OLD_LORAS=(
    "mix4.safetensors"
    "shiyuanlimei_v1.0.safetensors"
    "shiyuanlimei.safetensors"
)

for dir in "${LORA_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Checking directory: $dir"
        for lora in "${OLD_LORAS[@]}"; do
            filepath="$dir/$lora"
            if [ -f "$filepath" ] && [ ! -L "$filepath" ]; then
                # It's a regular file (not a symlink), remove it
                echo "Removing old LoRA file: $filepath"
                rm -f "$filepath"
            elif [ -L "$filepath" ]; then
                echo "Keeping symlink: $filepath -> $(readlink $filepath)"
            fi
        done
    fi
done

echo "Cleanup complete!"
echo ""
echo "The system will now use the symlink strategy:"
echo "- Your custom LoRA (e.g., korean_neurocanvas_v1.safetensors) stays as is"
echo "- A symlink named 'mix4.safetensors' points to your custom LoRA"
echo "- ComfyUI thinks it's loading 'mix4.safetensors' but gets your custom LoRA"