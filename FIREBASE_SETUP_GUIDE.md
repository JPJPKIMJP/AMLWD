# 🔥 Firebase Setup Guide for AMLWD

## Step 1: Create Firebase Project (Web Console)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"**
3. Enter project name: `amlwd-image-gen` (or your preferred name)
4. Disable Google Analytics (not needed for this)
5. Click **"Create Project"**

## Step 2: Install Firebase CLI

Open your terminal and run:
```bash
npm install -g firebase-tools
```

## Step 3: Login and Initialize

```bash
# Login to Firebase
firebase login

# Navigate to firebase directory
cd /mnt/c/Users/goooo/AMLWD/firebase

# Initialize Firebase in this directory
firebase init
```

When running `firebase init`, select:
- ✅ **Functions** (Create and deploy Cloud Functions)
- ✅ **Hosting** (Configure files for Firebase Hosting)
- Use an existing project → Select `amlwd-image-gen`
- Functions language: **JavaScript**
- Use ESLint? **No**
- Install dependencies? **Yes**
- Public directory: `../` (parent directory)
- Single-page app? **Yes**
- Set up automatic builds? **No**

## Step 4: Set RunPod Credentials

First, set your RunPod credentials as environment variables:

```bash
# On Linux/Mac:
export RUNPOD_API_KEY="your-runpod-api-key"
export RUNPOD_ENDPOINT_ID="your-runpod-endpoint-id"

# On Windows:
set RUNPOD_API_KEY=your-runpod-api-key
set RUNPOD_ENDPOINT_ID=your-runpod-endpoint-id
```

Then set them in Firebase:

```bash
# Set your RunPod credentials as Firebase config
firebase functions:config:set runpod.api_key="$RUNPOD_API_KEY"
firebase functions:config:set runpod.endpoint_id="$RUNPOD_ENDPOINT_ID"
```

## Step 5: Install Function Dependencies

```bash
cd functions
npm install
cd ..
```

## Step 6: Deploy to Firebase

```bash
# Deploy everything (functions + hosting)
firebase deploy
```

## Step 7: Get Your URLs

After deployment, you'll see:
```
✔ Deploy complete!

Project Console: https://console.firebase.google.com/project/amlwd-image-gen/overview
Hosting URL: https://amlwd-image-gen.web.app
Function URL: https://us-central1-amlwd-image-gen.cloudfunctions.net/generateImage
```

## Step 8: Update Your Frontend

Edit `index-firebase.html` and replace:
```javascript
const API_URL = 'https://YOUR-FIREBASE-PROJECT.web.app/api';
```

With your actual project URL:
```javascript
const API_URL = 'https://amlwd-image-gen.web.app/api';
```

## Step 9: Test Your App

1. Visit: `https://amlwd-image-gen.web.app/index-firebase.html`
2. Enter a prompt
3. Click Generate
4. Wait for your AI image!

## Troubleshooting

### If deployment fails:
```bash
# Check Firebase login
firebase login --reauth

# Try deploying functions only
firebase deploy --only functions

# Try deploying hosting only
firebase deploy --only hosting
```

### To test locally:
```bash
# Start Firebase emulators
firebase emulators:start

# Visit: http://localhost:5000
```

### To view logs:
```bash
firebase functions:log
```

## Cost Information

Firebase Free Tier includes:
- 125,000 function invocations/month
- 5GB hosting storage
- 10GB/month hosting transfer

Your costs will mainly come from RunPod ($0.02-0.05 per image).

## Next Steps

1. Set up custom domain (optional)
2. Add authentication (optional)
3. Add image history/gallery
4. Add more AI models

---

Need help? Check [Firebase Documentation](https://firebase.google.com/docs)