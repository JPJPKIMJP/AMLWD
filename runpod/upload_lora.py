#!/usr/bin/env python3
"""
Simple HTTP server to upload LoRA files to RunPod volume
Run this on a RunPod pod to easily upload LoRA files
"""

import os
import http.server
import socketserver
import cgi
import json
from urllib.parse import parse_qs, urlparse

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>LoRA Upload to RunPod</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .upload-area {
            border: 2px dashed #4CAF50;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            background: #f9f9f9;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            background: #e8f5e9;
            border-color: #2E7D32;
        }
        .upload-area.dragover {
            background: #e8f5e9;
            border-color: #2E7D32;
        }
        #file-input {
            display: none;
        }
        .file-info {
            margin: 20px 0;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 5px;
            display: none;
        }
        .upload-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            display: none;
            margin: 0 auto;
        }
        .upload-btn:hover {
            background: #45a049;
        }
        .upload-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .status {
            margin: 20px 0;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .lora-list {
            margin-top: 30px;
        }
        .lora-item {
            padding: 10px;
            margin: 5px 0;
            background: #f0f0f0;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .delete-btn {
            background: #f44336;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .delete-btn:hover {
            background: #d32f2f;
        }
        .progress {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
            display: none;
        }
        .progress-bar {
            height: 100%;
            background: #4CAF50;
            width: 0%;
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Upload LoRA to RunPod Volume</h1>
        
        <div class="upload-area" id="upload-area">
            <p>📁 Click to select or drag & drop your LoRA file here</p>
            <p style="color: #666; font-size: 14px;">Supports .safetensors files</p>
        </div>
        
        <input type="file" id="file-input" accept=".safetensors">
        
        <div class="file-info" id="file-info">
            <strong>Selected file:</strong> <span id="file-name"></span><br>
            <strong>Size:</strong> <span id="file-size"></span>
        </div>
        
        <div class="progress" id="progress">
            <div class="progress-bar" id="progress-bar"></div>
        </div>
        
        <button class="upload-btn" id="upload-btn" onclick="uploadFile()">Upload LoRA</button>
        
        <div class="status" id="status"></div>
        
        <div class="lora-list">
            <h3>Existing LoRAs:</h3>
            <div id="lora-files"></div>
        </div>
    </div>
    
    <script>
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const fileInfo = document.getElementById('file-info');
        const uploadBtn = document.getElementById('upload-btn');
        const status = document.getElementById('status');
        const progress = document.getElementById('progress');
        const progressBar = document.getElementById('progress-bar');
        
        let selectedFile = null;
        
        // File selection
        uploadArea.onclick = () => fileInput.click();
        
        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                selectedFile = file;
                document.getElementById('file-name').textContent = file.name;
                document.getElementById('file-size').textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
                fileInfo.style.display = 'block';
                uploadBtn.style.display = 'block';
            }
        };
        
        // Drag and drop
        uploadArea.ondragover = (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        };
        
        uploadArea.ondragleave = () => {
            uploadArea.classList.remove('dragover');
        };
        
        uploadArea.ondrop = (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const file = e.dataTransfer.files[0];
            if (file && file.name.endsWith('.safetensors')) {
                selectedFile = file;
                document.getElementById('file-name').textContent = file.name;
                document.getElementById('file-size').textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
                fileInfo.style.display = 'block';
                uploadBtn.style.display = 'block';
            } else {
                showStatus('Please select a .safetensors file', 'error');
            }
        };
        
        function showStatus(message, type) {
            status.textContent = message;
            status.className = 'status ' + type;
            status.style.display = 'block';
        }
        
        async function uploadFile() {
            if (!selectedFile) return;
            
            uploadBtn.disabled = true;
            progress.style.display = 'block';
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {
                const xhr = new XMLHttpRequest();
                
                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        progressBar.style.width = percentComplete + '%';
                    }
                };
                
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        showStatus('LoRA uploaded successfully!', 'success');
                        loadLoraList();
                        setTimeout(() => {
                            fileInfo.style.display = 'none';
                            uploadBtn.style.display = 'none';
                            progress.style.display = 'none';
                            progressBar.style.width = '0%';
                            fileInput.value = '';
                            selectedFile = null;
                        }, 2000);
                    } else {
                        showStatus('Upload failed: ' + xhr.responseText, 'error');
                    }
                    uploadBtn.disabled = false;
                };
                
                xhr.onerror = function() {
                    showStatus('Upload failed: Network error', 'error');
                    uploadBtn.disabled = false;
                };
                
                xhr.open('POST', '/upload');
                xhr.send(formData);
                
            } catch (error) {
                showStatus('Upload failed: ' + error.message, 'error');
                uploadBtn.disabled = false;
            }
        }
        
        async function deleteLoRA(filename) {
            if (!confirm('Delete ' + filename + '?')) return;
            
            try {
                const response = await fetch('/delete?file=' + encodeURIComponent(filename), {
                    method: 'POST'
                });
                
                if (response.ok) {
                    showStatus('Deleted ' + filename, 'success');
                    loadLoraList();
                } else {
                    showStatus('Failed to delete', 'error');
                }
            } catch (error) {
                showStatus('Delete failed: ' + error.message, 'error');
            }
        }
        
        async function loadLoraList() {
            try {
                const response = await fetch('/list');
                const files = await response.json();
                
                const container = document.getElementById('lora-files');
                if (files.length === 0) {
                    container.innerHTML = '<p style="color: #666;">No LoRA files found</p>';
                } else {
                    container.innerHTML = files.map(file => 
                        `<div class="lora-item">
                            <span>${file}</span>
                            <button class="delete-btn" onclick="deleteLoRA('${file}')">Delete</button>
                        </div>`
                    ).join('');
                }
            } catch (error) {
                console.error('Failed to load LoRA list:', error);
            }
        }
        
        // Load list on page load
        loadLoraList();
    </script>
</body>
</html>
"""

class LoRAUploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif parsed_path.path == '/list':
            self.list_loras()
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/upload':
            self.upload_lora()
        elif parsed_path.path == '/delete':
            self.delete_lora()
        else:
            self.send_error(404)
    
    def upload_lora(self):
        try:
            content_type, pdict = cgi.parse_header(self.headers['Content-Type'])
            if content_type == 'multipart/form-data':
                pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
                fields = cgi.parse_multipart(self.rfile, pdict)
                
                if 'file' in fields:
                    file_data = fields['file'][0]
                    # Get filename from content-disposition or use default
                    filename = "uploaded_lora.safetensors"
                    
                    # Try to extract filename from headers
                    if 'Content-Disposition' in self.headers:
                        import re
                        filename_match = re.search(r'filename="([^"]+)"', self.headers['Content-Disposition'])
                        if filename_match:
                            filename = filename_match.group(1)
                    
                    # Ensure it's a safetensors file
                    if not filename.endswith('.safetensors'):
                        self.send_error(400, "Only .safetensors files are allowed")
                        return
                    
                    # Save to LoRA directory
                    lora_dir = "/workspace/ComfyUI/models/loras"
                    if not os.path.exists(lora_dir):
                        lora_dir = "/runpod-volume/ComfyUI/models/loras"
                    
                    os.makedirs(lora_dir, exist_ok=True)
                    filepath = os.path.join(lora_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Uploaded {filename} successfully".encode())
                else:
                    self.send_error(400, "No file provided")
            else:
                self.send_error(400, "Invalid content type")
        except Exception as e:
            self.send_error(500, str(e))
    
    def list_loras(self):
        try:
            lora_dir = "/workspace/ComfyUI/models/loras"
            if not os.path.exists(lora_dir):
                lora_dir = "/runpod-volume/ComfyUI/models/loras"
            
            if os.path.exists(lora_dir):
                files = [f for f in os.listdir(lora_dir) if f.endswith('.safetensors')]
            else:
                files = []
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def delete_lora(self):
        try:
            query = parse_qs(urlparse(self.path).query)
            if 'file' not in query:
                self.send_error(400, "No file specified")
                return
            
            filename = query['file'][0]
            if not filename.endswith('.safetensors'):
                self.send_error(400, "Invalid file")
                return
            
            lora_dir = "/workspace/ComfyUI/models/loras"
            if not os.path.exists(lora_dir):
                lora_dir = "/runpod-volume/ComfyUI/models/loras"
            
            filepath = os.path.join(lora_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Deleted successfully")
            else:
                self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == "__main__":
    PORT = 8080
    
    print(f"Starting LoRA upload server on port {PORT}")
    print(f"Access at: http://localhost:{PORT}")
    print("\nIf running on RunPod, you may need to:")
    print("1. Use RunPod's proxy URL")
    print("2. Or SSH tunnel: ssh -L 8080:localhost:8080 root@<pod-ip>")
    
    with socketserver.TCPServer(("", PORT), LoRAUploadHandler) as httpd:
        httpd.serve_forever()