# Docker Hub Setup for GitHub Actions

## Steps to Enable Automatic Docker Builds:

### 1. Create Docker Hub Access Token
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name it "GitHub Actions"
4. Copy the token (you'll only see it once!)

### 2. Add Secrets to GitHub Repository
1. Go to your repository: https://github.com/JPJPKIMJP/AMLWD
2. Click Settings → Secrets and variables → Actions
3. Add these secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username (jpjpkimjp)
   - `DOCKER_TOKEN`: The access token from step 1

### 3. Trigger the Build
Once secrets are added, the workflow will automatically build when:
- You push changes to Dockerfile.flux
- You push changes to any file in runpod/src/
- You manually trigger it from Actions tab

### Manual Trigger:
1. Go to https://github.com/JPJPKIMJP/AMLWD/actions
2. Click "Build and Push FLUX Docker Image"
3. Click "Run workflow"
4. Select branch: main
5. Click "Run workflow"

The build will take ~10-15 minutes and push to:
- `jpjpkimjp/flux-comfyui:latest`