# 🔐 Firebase Secure Setup Guide

## What You Need to Do in Firebase Console

### 1. Enable Authentication (5 minutes)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **amlwd-image-gen**
3. Click **Authentication** in the left menu
4. Click **Get started**
5. Enable these sign-in methods:
   - **Email/Password**: 
     - Click on it → Enable → Save
   - **Google** (optional but recommended):
     - Click on it → Enable
     - Select your project support email
     - Save

### 2. Enable Firestore Database (3 minutes)

1. In Firebase Console, click **Firestore Database**
2. Click **Create database**
3. Choose **Start in production mode**
4. Select your location (use default)
5. Click **Create**

### 3. Get Your Firebase Web Config (2 minutes)

1. In Firebase Console, click the **gear icon** → **Project settings**
2. Scroll down to **Your apps**
3. If no web app exists:
   - Click **</> Web** icon
   - Name it: "AMLWD Web App"
   - Click **Register app**
4. Copy the firebaseConfig object:

```javascript
const firebaseConfig = {
  apiKey: "...",
  authDomain: "amlwd-image-gen.firebaseapp.com",
  projectId: "amlwd-image-gen",
  storageBucket: "amlwd-image-gen.appspot.com",
  messagingSenderId: "...",
  appId: "..."
};
```

### 4. Set Firestore Security Rules (1 minute)

1. Go to **Firestore Database** → **Rules** tab
2. Replace with these rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Only authenticated users can read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Image generation logs - only readable by the user who created them
    match /image_generations/{document} {
      allow read: if request.auth != null && request.auth.uid == resource.data.userId;
      allow write: if false; // Only cloud functions can write
    }
    
    // API keys collection - no client access
    match /api_keys/{document} {
      allow read, write: if false;
    }
  }
}
```

3. Click **Publish**

### 5. Deploy the Secure Function (5 minutes)

Run these commands in your terminal:

```bash
# 1. Make sure you have your RunPod credentials
export RUNPOD_API_KEY="your-runpod-api-key"
export RUNPOD_ENDPOINT_ID="your-runpod-endpoint-id"

# 2. Navigate to project
cd ~/AMLWD

# 3. Replace the old function with secure version
cp firebase/functions/index-secure.js firebase/functions/index.js

# 4. Update the frontend with your Firebase config
# Edit firebase-secure-frontend.html and replace the firebaseConfig object

# 5. Deploy everything
cd firebase
firebase functions:config:set runpod.api_key="$RUNPOD_API_KEY"
firebase functions:config:set runpod.endpoint_id="$RUNPOD_ENDPOINT_ID"
firebase deploy
```

## Testing Your Secure Setup

1. Open: `https://amlwd-image-gen.web.app/firebase-secure-frontend.html`
2. Create an account with email/password
3. Try generating an image
4. Check daily limit (10 images per user)

## What This Gives You

✅ **User Authentication Required** - No anonymous access
✅ **Rate Limiting** - 10 images per user per day
✅ **Usage Tracking** - Know who generates what
✅ **Secure API** - RunPod keys never exposed
✅ **Firestore Logs** - Full audit trail

## Monitoring Usage

1. Go to **Firestore Database** in Firebase Console
2. Look at:
   - `users` collection - See all users and their request counts
   - `image_generations` collection - See all generated images

## Optional: Adding More Security

### Enable App Check (Prevents bot attacks)
1. Go to **App Check** in Firebase Console
2. Register your app
3. Add to your function:
```javascript
const appCheck = require('firebase-admin/app-check');
// Verify app check token
```

### Add Custom Claims (Admin users)
```javascript
// Give certain users more quota
admin.auth().setCustomUserClaims(uid, { premium: true });
```

## Costs

- **Firebase Auth**: Free for 10K users/month
- **Firestore**: Free for 50K reads/day
- **Functions**: Free for 125K invocations/month
- **RunPod**: Your existing costs

## Support

- Check function logs: `firebase functions:log`
- Test locally: `firebase emulators:start`
- Debug auth: Check Firebase Console → Authentication