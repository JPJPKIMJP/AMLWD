# Docker Hub Setup for GitHub Actions

## Current Status
- GitHub Actions workflow is **ENABLED** at `.github/workflows/docker-build.yml`
- Builds are **FAILING** because Docker Hub secrets are not configured

## To Fix the Builds

### 1. Get Docker Hub Access Token
1. Go to https://hub.docker.com and log in with username: jpjpkimjp
2. Click your username (top right) → **Account Settings**
3. Click **Security** in the left sidebar
4. Click **New Access Token**
5. Description: "GitHub Actions AMLWD"
6. Click **Generate**
7. **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)

### 2. Add to GitHub Repository
1. Go to https://github.com/JPJPKIMJP/AMLWD/settings/secrets/actions
2. Click **New repository secret**
3. Add:
   - Name: `DOCKER_USERNAME`
   - Secret: `jpjpkimjp`
4. Click **New repository secret** again
5. Add:
   - Name: `DOCKER_TOKEN`
   - Secret: [Paste the token from Docker Hub]

### 3. Test the Build
1. Go to https://github.com/JPJPKIMJP/AMLWD/actions
2. Click "Build and Push FLUX Docker Image"
3. Click **Run workflow** → **Run workflow**

## What This Does
- Automatically builds the FLUX Docker image when you update:
  - `runpod/Dockerfile.flux`
  - `runpod/src/**` 
  - `runpod/start.sh`
- Pushes to Docker Hub as `jpjpkimjp/flux-comfyui:latest`

## Manual Build (Alternative)
If you prefer to build manually instead:
```bash
cd /Users/jpsmac/AMLWD/runpod
docker build -f Dockerfile.flux -t jpjpkimjp/flux-comfyui:latest .
docker push jpjpkimjp/flux-comfyui:latest
```