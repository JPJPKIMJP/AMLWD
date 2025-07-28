#!/usr/bin/env python3
"""
Simple file server for RunPod upload
Run this on your Mac, then wget from RunPod
"""
import http.server
import socketserver
import socket
import os

# Get your Mac's IP address
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "localhost"
    finally:
        s.close()
    return ip

PORT = 9999  # Changed to 9999 to avoid conflicts

# Change to the directory with our files
os.chdir('/Users/jpsmac/AMLWD/runpod/volume_update')

Handler = http.server.SimpleHTTPRequestHandler

print("Starting file server...")
print("=" * 60)
print("IMPORTANT: Run these commands in your RUNPOD TERMINAL, not here!")
print("=" * 60)
print(f"\nCommands for RunPod:\n")

ip = get_ip()
print(f"cd /workspace")
print(f"wget http://{ip}:{PORT}/flux_handler.py")
print(f"wget http://{ip}:{PORT}/flux_with_lora.json")
print(f"wget http://{ip}:{PORT}/start_volume.sh")
print(f"chmod +x start_volume.sh")
print(f"\nThen update your endpoint's Container Start Command to: /workspace/start_volume.sh")
print(f"\n{'=' * 60}")
print(f"Server running on: http://{ip}:{PORT}")
print(f"Press Ctrl+C to stop the server when done.\n")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()