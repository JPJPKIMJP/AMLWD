# 🔐 Secure RunPod Setup Guide

## Overview

This guide explains how to securely set up and deploy your RunPod serverless endpoint without exposing API keys in your code.

## Prerequisites

1. RunPod account with API access
2. Docker installed locally
3. Git installed
4. Node.js and npm (for Firebase deployment)

## Step 1: Get Your RunPod Credentials

1. Log in to [RunPod Console](https://www.runpod.io/console)
2. Go to **Settings** → **API Keys**
3. Create a new API key and save it securely
4. Deploy a serverless endpoint and note the endpoint ID

## Step 2: Set Up Environment Variables

### Option A: Using .env file (Recommended for local development)

1. Create a `.env` file in the project root:
   ```bash
   cd ~/AMLWD
   touch .env
   ```

2. Add your credentials to `.env`:
   ```
   RUNPOD_API_KEY=your-actual-api-key-here
   RUNPOD_ENDPOINT_ID=your-actual-endpoint-id-here
   MODEL_ID=runwayml/stable-diffusion-v1-5
   ```

3. The `.env` file is already in `.gitignore`, so it won't be committed

### Option B: Using system environment variables

**On Linux/Mac:**
```bash
export RUNPOD_API_KEY="your-actual-api-key-here"
export RUNPOD_ENDPOINT_ID="your-actual-endpoint-id-here"
export MODEL_ID="runwayml/stable-diffusion-v1-5"

# To make permanent, add to ~/.bashrc or ~/.zshrc
echo 'export RUNPOD_API_KEY="your-actual-api-key-here"' >> ~/.bashrc
echo 'export RUNPOD_ENDPOINT_ID="your-actual-endpoint-id-here"' >> ~/.bashrc
```

**On Windows:**
```cmd
set RUNPOD_API_KEY=your-actual-api-key-here
set RUNPOD_ENDPOINT_ID=your-actual-endpoint-id-here
set MODEL_ID=runwayml/stable-diffusion-v1-5

# To make permanent, use setx
setx RUNPOD_API_KEY "your-actual-api-key-here"
setx RUNPOD_ENDPOINT_ID "your-actual-endpoint-id-here"
```

## Step 3: Deploy RunPod Serverless Handler

1. Navigate to the runpod directory:
   ```bash
   cd ~/AMLWD/runpod
   ```

2. Build the Docker image:
   ```bash
   docker build -t your-dockerhub-username/amlwd-runpod:latest .
   ```

3. Push to Docker Hub:
   ```bash
   docker push your-dockerhub-username/amlwd-runpod:latest
   ```

4. Deploy to RunPod:
   ```bash
   # The deploy.sh script will use your environment variables
   ./deploy.sh
   ```

## Step 4: Set Up Backend API

1. Navigate to backend directory:
   ```bash
   cd ~/AMLWD/backend
   ```

2. Create `.env` file with your credentials:
   ```
   RUNPOD_API_KEY=your-actual-api-key-here
   RUNPOD_ENDPOINT_ID=your-actual-endpoint-id-here
   ```

3. Run locally for testing:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

4. Or use Docker:
   ```bash
   docker build -t amlwd-backend .
   docker run -p 8000:8000 --env-file .env amlwd-backend
   ```

## Step 5: Firebase Deployment (Optional)

If using Firebase Functions as your backend:

1. Navigate to project root:
   ```bash
   cd ~/AMLWD
   ```

2. Run the setup script (it will use your environment variables):
   ```bash
   # On Linux/Mac:
   ./firebase-setup.sh
   
   # On Windows:
   firebase-setup.bat
   ```

3. The script will automatically:
   - Check for environment variables
   - Set them in Firebase config
   - Deploy your functions

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate keys regularly** if exposed
4. **Use separate keys** for development and production
5. **Monitor API usage** in RunPod dashboard
6. **Set spending limits** in RunPod to prevent unexpected charges

## GitHub Actions Deployment

For automated deployment via GitHub Actions:

1. Go to your GitHub repository settings
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following repository secrets:
   - `RUNPOD_API_KEY`
   - `RUNPOD_ENDPOINT_ID`
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`

The GitHub Actions workflow will use these secrets for secure deployment.

## Troubleshooting

### "API key not found" error
- Ensure environment variables are set correctly
- Check if `.env` file is in the correct location
- Verify the variable names match exactly

### "Endpoint not found" error
- Verify the endpoint ID is correct
- Ensure the endpoint is active in RunPod console
- Check if you have the correct permissions

### Docker build fails
- Ensure Docker is running
- Check if you're logged in to Docker Hub
- Verify Dockerfile syntax is correct

## Support

For issues specific to:
- **RunPod**: Check [RunPod Documentation](https://docs.runpod.io)
- **Firebase**: See [Firebase Documentation](https://firebase.google.com/docs)
- **This project**: Open an issue on GitHub