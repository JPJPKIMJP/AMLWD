# RunPod Network Volume Update Instructions

This method updates your RunPod deployment WITHOUT rebuilding Docker.

## Prerequisites
- You must have a RunPod Network Volume attached to your endpoint
- The volume should be mounted at `/workspace` or `/runpod-volume`

## Step 1: Upload Files to RunPod

You need to upload these files to your RunPod network volume:
- `flux_handler.py` - Updated handler with LoRA support
- `flux_with_lora.json` - LoRA workflow
- `start_volume.sh` - Updated startup script

### Option A: Using RunPod Web Console
1. Go to RunPod dashboard
2. Navigate to your Network Volume
3. Use the file browser to upload the files

### Option B: Using a Running Pod
1. Start a GPU pod with your network volume attached
2. Use the terminal to download files:

```bash
# In RunPod terminal
cd /workspace

# Download updated handler
wget https://raw.githubusercontent.com/YOUR_GITHUB/YOUR_REPO/main/runpod/volume_update/flux_handler.py

# Download LoRA workflow
wget https://raw.githubusercontent.com/YOUR_GITHUB/YOUR_REPO/main/runpod/volume_update/flux_with_lora.json

# Download updated start script
wget https://raw.githubusercontent.com/YOUR_GITHUB/YOUR_REPO/main/runpod/volume_update/start_volume.sh
chmod +x start_volume.sh
```

### Option C: Using SCP/SFTP
If you have SSH access to a pod:
```bash
scp flux_handler.py root@YOUR_POD_IP:/workspace/
scp flux_with_lora.json root@YOUR_POD_IP:/workspace/
scp start_volume.sh root@YOUR_POD_IP:/workspace/
```

## Step 2: Update Your Endpoint

1. Go to RunPod Serverless dashboard
2. Edit your endpoint
3. In the "Container Start Command", change it to:
   ```
   /workspace/start_volume.sh
   ```
   OR if your volume is at /runpod-volume:
   ```
   /runpod-volume/start_volume.sh
   ```

## Step 3: Restart Workers

1. Scale workers to 0
2. Wait 30 seconds
3. Scale workers back to 1

## Step 4: Test

The LoRA feature should now work! Test with:
- Select "Shiyuanlimei v1.0" in the web UI
- Generate an image

## What This Does

The updated `start_volume.sh` will:
1. Use the existing Docker image
2. Copy the updated handler from the volume
3. Download the LoRA if not present
4. Start with LoRA support enabled

## Benefits

✅ No Docker rebuild needed
✅ Updates take effect immediately
✅ Can update handler anytime by replacing the file in volume
✅ LoRAs are downloaded on first use