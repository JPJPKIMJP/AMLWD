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
   firebase functions:config:set runpod.api_key="rpa_FK9XB61YQGYODPNXBWE21FHKXYVY3V6V1DA7HB111sncts"
   firebase functions:config:set runpod.endpoint_id="6f3dkzdg44elpj"
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