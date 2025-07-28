# Secure S3 Setup with Firebase

## Overview
This setup stores S3 credentials securely in Firebase and RunPod fetches them at runtime, avoiding hardcoded credentials.

## Architecture
1. S3 credentials stored in Firebase Functions config
2. Firebase Cloud Function provides credentials via secure endpoint
3. RunPod handler fetches credentials on startup
4. Falls back to environment variables if Firebase unavailable

## Setup Steps

### 1. Configure Firebase (One-time setup)

```bash
cd firebase
./setup-s3-credentials.sh
```

This sets:
- `s3volume.endpoint`
- `s3volume.bucket`
- `s3volume.access_key`
- `s3volume.secret_key`

### 2. Deploy Firebase Functions

```bash
cd firebase
firebase deploy --only functions
```

This deploys the `getS3Credentials` function.

### 3. Configure RunPod

Add only ONE environment variable to RunPod:
- `RUNPOD_API_KEY`: Your RunPod API key (used for authentication)

That's it! No S3 credentials needed in RunPod.

## How It Works

1. **On RunPod startup**:
   - Handler calls Firebase `getS3Credentials` endpoint
   - Authenticates using `RUNPOD_API_KEY`
   - Receives S3 credentials securely
   - Configures S3 client

2. **Security**:
   - S3 credentials never stored in RunPod
   - Firebase endpoint requires authentication
   - Credentials fetched over HTTPS
   - Falls back gracefully if Firebase unavailable

3. **LoRA Storage**:
   - LoRAs uploaded to S3 volume
   - Persist across pod restarts
   - Downloaded on-demand when needed

## Testing

1. Check Firebase function:
```bash
curl https://us-central1-amlwd-image-gen.cloudfunctions.net/getS3Credentials \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY"
```

2. Check RunPod logs for:
```
Fetching S3 credentials from Firebase...
Successfully fetched S3 credentials from Firebase
Using S3 credentials from Firebase
S3 volume client configured for bucket: 82elxnhs55
```

## Advantages

- ✅ No S3 credentials in RunPod environment
- ✅ Centralized credential management
- ✅ Easy to update credentials (just update Firebase)
- ✅ More secure than environment variables
- ✅ Automatic fallback to env vars if needed

## Troubleshooting

If S3 not working:
1. Check Firebase function logs
2. Verify RUNPOD_API_KEY is set in RunPod
3. Check RunPod handler logs
4. Verify Firebase function is deployed
5. Test the credentials endpoint manually