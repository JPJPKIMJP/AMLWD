# FLUX Deployment Guide

## 🚀 Automated Deployment Process

### Prerequisites
- Git configured with GitHub
- RunPod account with serverless endpoint
- Docker Hub account (optional)
- Firebase CLI installed

### Step 1: Run Deployment Script
```bash
./deploy_to_runpod.sh
```

This script will:
1. ✅ Run all validation tests
2. ✅ Check for uncommitted changes
3. ✅ Build/push Docker image
4. ✅ Provide deployment instructions

### Step 2: Configure RunPod
1. Go to [RunPod Serverless](https://www.runpod.ai/console/serverless)
2. Update your endpoint:
   - Container: `jpjpkimjp/flux-comfyui:latest`
   - GPU: 24GB VRAM minimum
   - Workers: Start with 0-1 for testing

### Step 3: Set Environment Variables
```bash
# In RunPod endpoint settings:
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=your_bucket_name
R2_PUBLIC_URL=https://your-public-url.com
```

### Step 4: Test Deployment
```bash
# Set environment variables locally
export RUNPOD_API_KEY="your_api_key"
export RUNPOD_ENDPOINT_ID="your_endpoint_id"

# Run test
./test_deployment.sh
```

## 📊 Monitoring

### Real-time Monitoring
```bash
# Interactive monitor
./monitor_deployment.sh

# Continuous monitoring
./monitor_deployment.sh --continuous

# Full diagnostic
./monitor_deployment.sh --diagnostic
```

### Check Logs
```bash
# Firebase logs
firebase functions:log --only generateImageSecure -n 50

# RunPod logs (get worker ID from monitor)
runpod logs <worker-id> -f
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Timeout Errors
- Check all three timeout values:
  - Firebase: 540s
  - Client: 540000ms
  - Handler: 300s

#### 2. Model Not Found
```bash
# On RunPod pod (not serverless)
ls -la /workspace/ComfyUI/models/diffusion_models/
```

#### 3. Worker Not Starting
- Check GPU availability
- Verify Docker image exists
- Check environment variables

### Emergency Rollback
```bash
# Quick rollback to previous version
./rollback.sh
```

## 💰 Cost Optimization

### Testing Strategy
1. **Start Small**
   ```json
   {
     "prompt": "simple test",
     "width": 512,
     "height": 512
   }
   ```

2. **Scale Workers Carefully**
   - Development: 0-1 workers
   - Testing: 1-2 workers
   - Production: 2-5 workers

3. **Monitor Usage**
   ```bash
   # Check worker utilization
   ./monitor_deployment.sh
   ```

## 📋 Deployment Checklist

Before each deployment:
- [ ] Run `./deploy_to_runpod.sh`
- [ ] All tests pass
- [ ] Docker image built/pushed
- [ ] RunPod endpoint updated
- [ ] Environment variables set
- [ ] Workers scaled to 1
- [ ] Test generation works
- [ ] Logs look clean

## 🛡️ Security

1. **Never commit credentials**
   ```bash
   # Check for secrets
   git grep -i "api_key\|secret\|password"
   ```

2. **Use environment variables**
   - Store in RunPod dashboard
   - Never in code

3. **Monitor access**
   - Check Firebase auth logs
   - Monitor RunPod usage

## 📈 Performance Tuning

### Optimize Generation Time
1. **Reduce dimensions** for testing
2. **Lower steps** (10-15 vs 20)
3. **Pre-warm workers** for production

### Monitor Performance
```bash
# Time a generation
time ./test_deployment.sh

# Check model load time in logs
./monitor_deployment.sh --diagnostic
```

## 🔄 Continuous Deployment

### GitHub Actions Workflow
The repository includes automated Docker builds:
1. Push to main branch
2. GitHub Actions builds Docker image
3. Pushes to Docker Hub
4. Update RunPod to use new image

### Manual Updates
```bash
# Update and deploy
git add .
git commit -m "Update: description"
git push origin main

# Wait for Docker build
# Then update RunPod endpoint
```

## 📞 Support

### Getting Help
1. Check `DEBUGGING_GUIDE.md`
2. Review logs with monitoring script
3. Test with simulation locally
4. Create GitHub issue with:
   - Error messages
   - Log outputs
   - Configuration details

### Useful Commands
```bash
# Full system check
./monitor_deployment.sh --diagnostic > diagnostic.log

# Test minimal workflow
python3 validate_workflows.py

# Check handler locally
python3 test_handler_locally.py
```

Remember: Always test locally first, deploy to staging, then production!