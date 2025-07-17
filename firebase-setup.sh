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
firebase functions:config:set runpod.api_key="rpa_FK9XB61YQGYODPNXBWE21FHKXYVY3V6V1DA7HB111sncts"
firebase functions:config:set runpod.endpoint_id="6f3dkzdg44elpj"

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