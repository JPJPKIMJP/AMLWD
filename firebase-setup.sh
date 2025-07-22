#!/bin/bash

echo "🔥 AMLWD Firebase Setup"
echo "======================"
echo ""

# Check if firebase-tools is installed
if ! command -v firebase &> /dev/null; then
    echo "📦 Installing Firebase CLI..."
    npm install -g firebase-tools
fi

echo "📝 Step 1: Login to Firebase"
echo "----------------------------"
firebase login

echo ""
echo "📝 Step 2: Initialize Firebase Project"
echo "-------------------------------------"
cd firebase
firebase init

echo ""
echo "📝 Step 3: Setting RunPod Credentials"
echo "------------------------------------"
echo "Setting your RunPod API credentials..."

# Check for environment variables
if [ -z "$RUNPOD_API_KEY" ] || [ -z "$RUNPOD_ENDPOINT_ID" ]; then
    echo "❌ Error: RunPod credentials not found!"
    echo ""
    echo "Please set the following environment variables:"
    echo "  export RUNPOD_API_KEY='your-runpod-api-key'"
    echo "  export RUNPOD_ENDPOINT_ID='your-runpod-endpoint-id'"
    echo ""
    echo "Or create a .env file in the project root with:"
    echo "  RUNPOD_API_KEY=your-runpod-api-key"
    echo "  RUNPOD_ENDPOINT_ID=your-runpod-endpoint-id"
    exit 1
fi

firebase functions:config:set runpod.api_key="$RUNPOD_API_KEY"
firebase functions:config:set runpod.endpoint_id="$RUNPOD_ENDPOINT_ID"

echo ""
echo "📝 Step 4: Installing Dependencies"
echo "---------------------------------"
cd functions
npm install
cd ..

echo ""
echo "📝 Step 5: Deploy to Firebase"
echo "----------------------------"
firebase deploy

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Your app will be available at:"
echo "https://YOUR-PROJECT-ID.web.app"
echo ""
echo "Next steps:"
echo "1. Update index-firebase.html with your Firebase URL"
echo "2. Test image generation!"