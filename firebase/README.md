# Firebase Setup for AMLWD

## Quick Setup

1. **Install Firebase CLI**
   ```bash
   npm install -g firebase-tools
   ```

2. **Login to Firebase**
   ```bash
   firebase login
   ```

3. **Initialize Firebase** (in this directory)
   ```bash
   firebase init
   ```
   - Choose: Functions and Hosting
   - Select your project or create new
   - Choose JavaScript
   - Use existing functions directory

4. **Set your RunPod credentials**
   ```bash
   # First, export your credentials as environment variables
   export RUNPOD_API_KEY="your-runpod-api-key"
   export RUNPOD_ENDPOINT_ID="your-runpod-endpoint-id"
   
   # Then set them in Firebase
   firebase functions:config:set runpod.api_key="$RUNPOD_API_KEY"
   firebase functions:config:set runpod.endpoint_id="$RUNPOD_ENDPOINT_ID"
   ```

5. **Deploy**
   ```bash
   cd functions && npm install
   cd ..
   firebase deploy
   ```

## After Deployment

Your app will be available at:
- `https://YOUR-PROJECT.web.app`
- `https://YOUR-PROJECT.firebaseapp.com`

The API endpoint will be:
- `https://YOUR-PROJECT.web.app/api/generate`

## Update Frontend

In your `index.html`, change the API URL to your Firebase URL:
```javascript
const API_URL = 'https://YOUR-PROJECT.web.app/api';
```

## Benefits

- ✅ Free hosting (with limits)
- ✅ Automatic HTTPS
- ✅ Secure API key storage
- ✅ No need to manage servers
- ✅ Scales automatically