#!/usr/bin/env python3
import base64
import os

print("Creating base64 encoded files for easy transfer...")

files = {
    'flux_handler.py': '/Users/jpsmac/AMLWD/runpod/volume_update/flux_handler.py',
    'flux_with_lora.json': '/Users/jpsmac/AMLWD/runpod/volume_update/flux_with_lora.json',
    'start_volume.sh': '/Users/jpsmac/AMLWD/runpod/volume_update/start_volume.sh'
}

print("\n# Run these commands in RunPod terminal:\n")
print("cd /workspace\n")

for filename, filepath in files.items():
    with open(filepath, 'rb') as f:
        content = f.read()
        b64 = base64.b64encode(content).decode('utf-8')
        
    print(f"# Create {filename}")
    print(f"echo '{b64}' | base64 -d > {filename}")
    if filename.endswith('.sh'):
        print(f"chmod +x {filename}")
    print()

print("# Then update your endpoint's Container Start Command to: /workspace/start_volume.sh")