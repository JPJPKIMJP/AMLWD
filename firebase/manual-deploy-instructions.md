# 🚀 Manual Firebase Functions Deployment Instructions

Due to Node.js version requirements, you'll need to deploy the Firebase Functions manually.

## Quick Deploy Steps:

1. **Open Terminal/Command Prompt**

2. **Navigate to Firebase directory:**
   ```bash
   cd /mnt/c/Users/goooo/AMLWD/firebase
   # or on Windows:
   cd C:\Users\goooo\AMLWD\firebase
   ```

3. **Deploy Functions:**
   ```bash
   firebase deploy --only functions
   ```

   If you see a Node.js version error, you need Node.js 20+:
   - Download from: https://nodejs.org/
   - Install Node.js 20 LTS or newer
   - Run the deploy command again

## What This Deploys:

✅ **Fixed generateImageSecure function** with:
- LoRA parameter passing (lora_name, lora_strength)
- Proper payload structure for RunPod
- Fix for 500 Internal Server Error

## Alternative: Deploy from GitHub Actions

If you have GitHub Actions set up for Firebase:
1. The push to main branch may trigger auto-deployment
2. Check your GitHub Actions tab for deployment status

## Verify Deployment:

After deployment, test at https://amlwd-image-gen.web.app/:
1. Select "Mix4" from LoRA dropdown
2. Generate an image
3. Should work without 500 error!

## Current Code Status:
- ✅ Firebase Functions code updated with LoRA support
- ✅ RunPod workflow fixed for CLIP validation
- ✅ All code pushed to GitHub
- ⏳ Just needs Firebase deployment to go live