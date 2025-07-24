# FLUX Debugging Guide

## Before Every Deployment

1. **Run Local Tests**
   ```bash
   # Test handler locally
   python test_handler_locally.py
   
   # Run pre-deployment checks
   python test_before_deploy.py
   ```

2. **Review Changes**
   - Check for placeholder values (REPLACE_WITH_...)
   - Verify seed values are >= 0
   - Confirm timeout values are sufficient

## Common Issues and Solutions

### 1. Timeout Errors

**Symptoms:**
- "deadline-exceeded" error
- "Image generation timed out"
- Job still running on RunPod after error

**Solutions:**
```python
# Check these timeout values:
# 1. Firebase Function timeout (index.js)
.runWith({
    timeoutSeconds: 540,  # Should be 540 (9 min)
    memory: '2GB'
})

# 2. Client timeout (index.html)
httpsCallable('generateImageSecure', {
    timeout: 540000  # Should be 540000 (9 min)
})

# 3. Handler timeout (flux_handler.py)
def wait_for_image(self, prompt_id: str, timeout: int = 300)  # Should be >= 300
```

### 2. Workflow Validation Errors

**Symptoms:**
- "400 Client Error: Bad Request"
- "Value -1 smaller than min of 0: seed"

**Solutions:**
```python
# Check workflow JSON for:
# 1. Seed values
"seed": 0,  # Must be >= 0, not -1

# 2. Model names
"unet_name": "flux1-dev-kontext_fp8_scaled.safetensors",  # Not placeholder

# 3. Valid node connections
# Run: python -m json.tool src/workflows/flux_actual.json
```

### 3. Model Not Found

**Symptoms:**
- "Model not found" errors
- CLIP/VAE load but FLUX doesn't

**Solutions:**
```bash
# On RunPod pod (not serverless):
# 1. Find model location
find /workspace -name "*flux*.safetensors" -type f

# 2. Check diffusion_models directory
ls -la /workspace/ComfyUI/models/diffusion_models/

# 3. If missing, copy to correct location
cp /workspace/ComfyUI/models/checkpoints/flux*.safetensors \
   /workspace/ComfyUI/models/diffusion_models/
```

### 4. R2 Storage Issues

**Symptoms:**
- Images not uploading
- URLs not accessible

**Solutions:**
```bash
# Check R2 credentials in RunPod
echo $R2_ENDPOINT
echo $R2_BUCKET
echo $R2_PUBLIC_URL

# Test R2 directly
aws s3 ls s3://$R2_BUCKET/ --endpoint-url=$R2_ENDPOINT
```

## Testing Workflow

### 1. Local Simulation Testing
```bash
# Terminal 1: Start simulation server
python simulate_runpod.py

# Terminal 2: Run tests
python test_client.py

# Test specific scenario
SIMULATION_MODE=timeout python simulate_runpod.py
python test_client.py timeout
```

### 2. Staged Deployment Testing
```bash
# 1. Deploy to test endpoint first
git checkout -b test-deployment
# Make changes
git push origin test-deployment

# 2. Test with simple prompt
curl -X POST https://your-test-endpoint/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{"input": {"prompt": "simple test", "width": 512, "height": 512}}'

# 3. Only merge to main after testing
```

### 3. Production Debugging
```bash
# Check RunPod logs
runpod logs <worker-id> -f

# Check Firebase logs
firebase functions:log --only generateImageSecure -n 100

# Monitor R2 uploads
aws s3 ls s3://$R2_BUCKET/flux/ --endpoint-url=$R2_ENDPOINT --recursive
```

## Quick Fixes

### Force Restart Workers
```bash
# In RunPod dashboard
# Endpoint > Workers > Scale to 0
# Wait 30 seconds
# Scale back to desired number
```

### Clear Firebase Cache
```bash
firebase functions:delete generateImageSecure
firebase deploy --only functions:generateImageSecure
```

### Test Minimal Workflow
```python
# Create test_minimal.json with just UNETLoader
{
  "1": {
    "inputs": {
      "unet_name": "flux1-dev-kontext_fp8_scaled.safetensors"
    },
    "class_type": "UNETLoader"
  }
}
```

## Prevention Checklist

Before deploying:
- [ ] Run `test_handler_locally.py` - all tests pass
- [ ] Run `test_before_deploy.py` - all tests pass  
- [ ] No placeholder values in workflows
- [ ] All timeouts >= 300 seconds
- [ ] Seed values >= 0
- [ ] Test with simulation first
- [ ] Deploy to test endpoint before production
- [ ] Document any model/workflow changes

## Emergency Rollback

```bash
# Quick rollback to last working version
git log --oneline -10  # Find last working commit
git checkout <commit-hash>
firebase deploy

# Or use Firebase console to rollback function version
```