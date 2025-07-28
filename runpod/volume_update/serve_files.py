#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8888
os.chdir('/Users/jpsmac/AMLWD/runpod/volume_update')

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving files at http://localhost:{PORT}")
    print("Your local IP addresses:")
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"  http://{local_ip}:{PORT}")
    print("\nFiles available:")
    for f in os.listdir('.'):
        if not f.startswith('.'):
            print(f"  http://{local_ip}:{PORT}/{f}")
    httpd.serve_forever()