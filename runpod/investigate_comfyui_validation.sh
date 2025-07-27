#!/bin/bash

echo "Investigating ComfyUI LoRA validation..."
echo "======================================="
echo ""

# Search for validation patterns in ComfyUI
echo "Searching for LoRA validation in ComfyUI files..."

# Common ComfyUI directories
COMFYUI_DIRS=(
    "/workspace/ComfyUI"
    "/ComfyUI"
    "/runpod-volume/ComfyUI"
)

for dir in "${COMFYUI_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo ""
        echo "Searching in $dir..."
        
        # Search for the specific LoRA names in Python files
        echo "Looking for hardcoded LoRA names..."
        grep -r "mix4.safetensors\|shiyuanlimei_v1.0.safetensors" "$dir" --include="*.py" --include="*.json" 2>/dev/null | head -10
        
        # Search for validation patterns
        echo ""
        echo "Looking for LoRA validation patterns..."
        grep -r "Value not in list\|lora_name.*not in" "$dir" --include="*.py" 2>/dev/null | head -10
        
        # Check for node definitions
        echo ""
        echo "Looking for LoraLoader node definition..."
        find "$dir" -name "*.py" -exec grep -l "class.*LoraLoader\|LoraLoader.*=" {} \; 2>/dev/null | head -5
    fi
done

echo ""
echo "======================================="
echo "If validation is found in ComfyUI core files, we may need to:"
echo "1. Modify the ComfyUI installation"
echo "2. Use a custom node that doesn't have validation"
echo "3. Find the configuration that sets the allowed list"