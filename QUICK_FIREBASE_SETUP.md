# 🚀 Super Quick Firebase Setup (2 Steps!)

## Step 1: Create Firebase Project (2 minutes)

1. **Open this link:** https://console.firebase.google.com/u/0/project/_/overview?create
2. **Create project:**
   - Project name: `amlwd-image-gen`
   - Uncheck "Enable Google Analytics"
   - Click "Create Project"
   - Wait for creation (~30 seconds)
   - Click "Continue"

## Step 2: Run This Command (5 minutes)

Open terminal/command prompt in the AMLWD folder and run:

**Windows (Command Prompt):**
```cmd
cd C:\Users\goooo\AMLWD
firebase-quick-deploy.bat
```

**Windows (PowerShell) / Linux / Mac:**
```bash
cd /mnt/c/Users/goooo/AMLWD
./firebase-quick-deploy.sh
```

## That's it! 🎉

After deployment completes, your app will be live at:
```
https://amlwd-image-gen.web.app/index-firebase.html
```

## If You Get Errors:

1. **"Firebase not found"**
   ```bash
   npm install -g firebase-tools
   ```

2. **"Not logged in"**
   ```bash
   firebase login
   ```

3. **"Project not found"**
   - Make sure you created the project with exact name: `amlwd-image-gen`
   - Or update `.firebaserc` with your project name

## Test Your Deployment:

1. Visit: https://amlwd-image-gen.web.app/index-firebase.html
2. Enter prompt: "a cute robot painting a picture"
3. Click Generate
4. Wait ~30 seconds for your AI image!