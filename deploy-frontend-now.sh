#!/bin/bash

echo ""
echo "🚀 Deploying Frontend to Firebase Hosting..."
echo ""
echo "This will deploy the new UI features:"
echo "- LoRA deletion menu"
echo "- Generation progress visual"
echo "- Fixed date display"
echo "- Generation info menu"
echo ""

cd firebase
firebase deploy --only hosting

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Frontend deployed successfully!"
    echo ""
    echo "🌐 Live at: https://amlwd-image-gen.web.app/"
    echo ""
    echo "New features are now available:"
    echo "- Manage LoRAs button next to dropdown"
    echo "- Progress bar on Generate button"
    echo "- Info button in history items"
    echo "- Proper date display"
else
    echo ""
    echo "❌ Deployment failed."
    echo ""
    echo "Please ensure you have Node.js v20+ installed:"
    echo "https://nodejs.org/"
fi