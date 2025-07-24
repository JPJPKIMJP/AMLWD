#!/usr/bin/env python3
"""
RunPod Simulation Environment
Simulates various RunPod scenarios locally for testing
"""

import json
import time
import random
import base64
from flask import Flask, request, jsonify
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

# Global state
jobs = {}
queue = []
history = {}

# Simulation settings
SIMULATION_MODE = "normal"  # normal, slow, timeout, error, queue_stuck
FLUX_LOAD_TIME = 10  # seconds
FLUX_GEN_TIME = 120  # seconds

def log(msg):
    """Simulate RunPod logging"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

class ComfyUISimulator:
    """Simulates ComfyUI behavior"""
    
    def __init__(self):
        self.running = False
        self.current_prompt = None
        
    def process_prompt(self, prompt_id, workflow):
        """Simulate processing a workflow"""
        try:
            # Simulate different scenarios
            if SIMULATION_MODE == "error":
                time.sleep(2)
                history[prompt_id] = {
                    "status": "error",
                    "error": "Simulated ComfyUI error"
                }
                return
                
            if SIMULATION_MODE == "timeout":
                log(f"Starting timeout simulation for {prompt_id}")
                time.sleep(300)  # 5 minutes - will timeout
                return
                
            if SIMULATION_MODE == "slow":
                log(f"Starting SLOW generation for {prompt_id}")
                # Simulate slow model loading
                log("Loading FLUX model...")
                time.sleep(30)
                log("Model loaded, generating...")
                time.sleep(150)  # 2.5 minutes
            else:
                # Normal timing
                log(f"Loading FLUX model for {prompt_id}")
                time.sleep(FLUX_LOAD_TIME)
                log(f"Generating image for {prompt_id}")
                time.sleep(FLUX_GEN_TIME)
            
            # Simulate success
            history[prompt_id] = {
                "outputs": {
                    "8": {
                        "images": [{
                            "filename": f"ComfyUI_{prompt_id}.png",
                            "subfolder": "",
                            "type": "output"
                        }]
                    }
                },
                "status": "success"
            }
            log(f"Completed {prompt_id}")
            
        except Exception as e:
            log(f"Error processing {prompt_id}: {e}")
            history[prompt_id] = {"status": "error", "error": str(e)}

# ComfyUI endpoints
@app.route('/system_stats')
def system_stats():
    """Simulate ComfyUI system stats"""
    return jsonify({"system": {"python_version": "3.10"}})

@app.route('/prompt', methods=['POST'])
def queue_prompt():
    """Simulate ComfyUI prompt queueing"""
    data = request.json
    workflow = data.get('prompt', {})
    
    # Validate workflow
    for node_id, node in workflow.items():
        if node.get('class_type') == 'KSampler':
            seed = node['inputs'].get('seed', 0)
            if seed < 0:
                return jsonify({
                    "error": {
                        "type": "prompt_outputs_failed_validation",
                        "message": f"Value {seed} smaller than min of 0: seed"
                    }
                }), 400
    
    prompt_id = str(uuid.uuid4())
    
    if SIMULATION_MODE == "queue_stuck":
        log(f"Queue stuck simulation - not processing {prompt_id}")
        queue.append((1, prompt_id))
    else:
        # Start processing in background
        comfy = ComfyUISimulator()
        thread = threading.Thread(
            target=comfy.process_prompt,
            args=(prompt_id, workflow)
        )
        thread.start()
    
    return jsonify({"prompt_id": prompt_id})

@app.route('/history/<prompt_id>')
def get_history(prompt_id):
    """Simulate ComfyUI history endpoint"""
    if prompt_id in history:
        return jsonify({prompt_id: history[prompt_id]})
    return jsonify({})

@app.route('/queue')
def get_queue():
    """Simulate ComfyUI queue endpoint"""
    return jsonify({
        "queue_running": queue,
        "queue_pending": []
    })

@app.route('/view')
def view_image():
    """Simulate image viewing"""
    # Return a small test image
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )

# RunPod handler endpoint
@app.route('/runsync', methods=['POST'])
def runpod_handler():
    """Simulate RunPod serverless endpoint"""
    job_id = f"sim-{uuid.uuid4().hex[:8]}"
    
    try:
        # Get input
        data = request.json
        job_input = data.get('input', {})
        
        log(f"RunPod job {job_id} started")
        log(f"Mode: {SIMULATION_MODE}")
        
        # Simulate the handler running
        if SIMULATION_MODE == "handler_error":
            return jsonify({
                "id": job_id,
                "status": "FAILED",
                "error": "400 Client Error: Bad Request for url: http://localhost:8188/prompt"
            })
        
        # Call our local ComfyUI
        prompt_response = queue_prompt()
        
        if prompt_response.status_code != 200:
            return jsonify({
                "id": job_id,
                "status": "FAILED",
                "error": prompt_response.json
            })
        
        prompt_id = prompt_response.json['prompt_id']
        
        # Wait for result (with timeout)
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if prompt_id in history:
                result = history[prompt_id]
                if result.get('status') == 'success':
                    return jsonify({
                        "id": job_id,
                        "status": "COMPLETED",
                        "output": {
                            "status": "success",
                            "image": "base64_test_image_data",
                            "model": "flux-dev"
                        }
                    })
                elif result.get('status') == 'error':
                    return jsonify({
                        "id": job_id,
                        "status": "FAILED",
                        "error": result.get('error', 'Unknown error')
                    })
            
            time.sleep(1)
        
        # Timeout
        return jsonify({
            "id": job_id,
            "status": "FAILED",
            "error": "Image generation timed out"
        })
        
    except Exception as e:
        return jsonify({
            "id": job_id,
            "status": "FAILED",
            "error": str(e)
        })

@app.route('/test_scenarios')
def test_scenarios():
    """List available test scenarios"""
    return jsonify({
        "scenarios": {
            "normal": "Normal successful generation (~2 min)",
            "slow": "Slow generation (~3 min)",
            "timeout": "Generation times out (>5 min)",
            "error": "ComfyUI returns error",
            "handler_error": "Handler fails immediately",
            "queue_stuck": "Job stuck in queue forever"
        },
        "current": SIMULATION_MODE,
        "usage": "Set SIMULATION_MODE variable to test different scenarios"
    })

if __name__ == '__main__':
    print("RunPod Simulation Server")
    print("========================")
    print(f"Current mode: {SIMULATION_MODE}")
    print("Change SIMULATION_MODE to test different scenarios")
    print("\nStarting on http://localhost:8188 (ComfyUI)")
    print("RunPod endpoint: http://localhost:5000/runsync")
    print("Test scenarios: http://localhost:5000/test_scenarios")
    
    # Run on port 8188 to simulate ComfyUI
    from werkzeug.serving import run_simple
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    
    # Run both servers
    app.run(port=5000, threaded=True)