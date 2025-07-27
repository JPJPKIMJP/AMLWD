#!/bin/bash
# Update RunPod handler without rebuilding Docker image
# This script updates the handler file in the RunPod volume

echo "🔄 Updating RunPod Handler"
echo "========================="

# This script should be run on the RunPod instance
# It updates the flux_handler.py file in the volume

HANDLER_URL="https://raw.githubusercontent.com/JPJPKIMJP/AMLWD/main/runpod/src/flux_handler.py"
HANDLER_PATH="/workspace/flux_handler.py"

echo "Downloading updated handler from GitHub..."
wget -O "$HANDLER_PATH" "$HANDLER_URL"

if [ $? -eq 0 ]; then
    echo "✅ Handler updated successfully!"
    echo ""
    echo "The handler will use the new code on the next request."
    echo "No restart needed - RunPod reloads the handler for each job."
else
    echo "❌ Failed to update handler"
    exit 1
fi

echo ""
echo "Handler features:"
echo "- ✅ Custom LoRA download from Firebase URLs"
echo "- ✅ Automatic LoRA caching"
echo "- ✅ Support for FLUX text-to-image and image-to-image"
echo ""
echo "Done!"