#!/usr/bin/env python3
"""
Upload LoRA files directly to RunPod pod via SSH
Requires: pip install paramiko
"""

import os
import sys
import paramiko
from pathlib import Path

# RunPod SSH configuration
RUNPOD_HOST = "YOUR_POD_IP"  # Replace with your pod's IP
RUNPOD_PORT = 22  # or custom SSH port if different
RUNPOD_USER = "root"
RUNPOD_PASSWORD = None  # Set if using password auth
RUNPOD_KEY_PATH = None  # Or path to SSH key

# Destination path on RunPod
LORA_DEST_PATH = "/workspace/ComfyUI/models/loras/"

def upload_lora(local_file_path, pod_ip, ssh_port=22, password=None, key_path=None):
    """Upload a LoRA file to RunPod volume"""
    
    # Validate file
    if not os.path.exists(local_file_path):
        print(f"❌ File not found: {local_file_path}")
        return False
    
    if not local_file_path.endswith('.safetensors'):
        print("❌ Only .safetensors files are supported")
        return False
    
    filename = os.path.basename(local_file_path)
    file_size = os.path.getsize(local_file_path) / (1024 * 1024)  # MB
    
    print(f"📁 Uploading: {filename} ({file_size:.2f} MB)")
    print(f"🎯 Target: {pod_ip}:{LORA_DEST_PATH}")
    
    try:
        # Setup SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect with password or key
        if key_path and os.path.exists(key_path):
            print("🔑 Using SSH key authentication")
            ssh.connect(pod_ip, port=ssh_port, username=RUNPOD_USER, 
                       key_filename=key_path)
        elif password:
            print("🔐 Using password authentication")
            ssh.connect(pod_ip, port=ssh_port, username=RUNPOD_USER, 
                       password=password)
        else:
            print("❌ No authentication method provided")
            return False
        
        # Create directory if needed
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {LORA_DEST_PATH}")
        stdout.read()
        
        # Setup SFTP
        sftp = ssh.open_sftp()
        
        # Upload with progress
        remote_path = os.path.join(LORA_DEST_PATH, filename)
        
        def progress_callback(transferred, total):
            percent = (transferred / total) * 100
            bar_length = 40
            filled = int(bar_length * transferred // total)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\r📤 Upload: [{bar}] {percent:.1f}%', end='', flush=True)
        
        # Upload file
        sftp.put(local_file_path, remote_path, callback=progress_callback)
        print()  # New line after progress
        
        # Verify upload
        try:
            remote_stat = sftp.stat(remote_path)
            remote_size = remote_stat.st_size / (1024 * 1024)
            print(f"✅ Upload complete! File size: {remote_size:.2f} MB")
            
            # List all LoRAs
            stdin, stdout, stderr = ssh.exec_command(f"ls -la {LORA_DEST_PATH}*.safetensors")
            files = stdout.read().decode().strip()
            if files:
                print("\n📂 Current LoRA files on pod:")
                print(files)
        except:
            print("⚠️  Could not verify upload")
        
        # Close connections
        sftp.close()
        ssh.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        return False

def main():
    print("🚀 RunPod LoRA Uploader")
    print("-" * 50)
    
    # Get pod IP
    pod_ip = input("Enter your RunPod pod IP address: ").strip()
    if not pod_ip:
        print("❌ Pod IP is required")
        return
    
    # Get SSH port
    ssh_port = input("Enter SSH port (default 22): ").strip()
    ssh_port = int(ssh_port) if ssh_port else 22
    
    # Get auth method
    auth_method = input("Auth method - (p)assword or (k)ey? [p/k]: ").strip().lower()
    
    password = None
    key_path = None
    
    if auth_method == 'k':
        key_path = input("Enter path to SSH private key: ").strip()
        if not os.path.exists(key_path):
            print("❌ SSH key file not found")
            return
    else:
        import getpass
        password = getpass.getpass("Enter SSH password: ")
    
    # Get LoRA file
    while True:
        lora_path = input("\nEnter path to LoRA file (or 'q' to quit): ").strip()
        
        if lora_path.lower() == 'q':
            break
            
        if lora_path.startswith('"') and lora_path.endswith('"'):
            lora_path = lora_path[1:-1]
        
        if upload_lora(lora_path, pod_ip, ssh_port, password, key_path):
            print("\n✨ LoRA ready to use in ComfyUI!")
            
            another = input("\nUpload another LoRA? [y/n]: ").strip().lower()
            if another != 'y':
                break
        else:
            retry = input("\nRetry? [y/n]: ").strip().lower()
            if retry != 'y':
                break
    
    print("\n👋 Done!")

if __name__ == "__main__":
    # Check if paramiko is installed
    try:
        import paramiko
    except ImportError:
        print("❌ paramiko not installed. Run: pip install paramiko")
        sys.exit(1)
    
    main()