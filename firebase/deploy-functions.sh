#!/bin/bash

echo "🚀 Deploying Firebase Functions with LoRA support..."
echo ""
echo "This script will deploy the updated Firebase Functions that include:"
echo "- LoRA parameter passing (lora_name, lora_strength)"
echo "- Fix for 500 Internal Server Error"
echo ""

# Check if firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found. Please install it first:"
    echo "npm install -g firebase-tools"
    exit 1
fi

# Navigate to firebase directory
cd "$(dirname "$0")"

# Deploy only functions
echo "📦 Deploying functions..."
firebase deploy --only functions --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Firebase Functions deployed successfully!"
    echo ""
    echo "🎯 LoRA functionality is now live:"
    echo "- Firebase Functions will pass lora_name and lora_strength to RunPod"
    echo "- The 500 error should be resolved"
    echo "- Test at: https://amlwd-image-gen.web.app/"
else
    echo ""
    echo "❌ Deployment failed. Please check the error above."
    echo ""
    echo "If you see a Node.js version error, you need to:"
    echo "1. Install Node.js v20 or higher"
    echo "2. Run this script again"
fi