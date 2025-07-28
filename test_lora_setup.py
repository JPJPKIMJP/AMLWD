#!/usr/bin/env python3
"""
Test script to verify LoRA setup in ComfyUI for FLUX
"""

import json
import requests
import os

def check_lora_workflow():
    """Check if the LoRA workflow is properly set up"""
    
    print("🔍 Checking LoRA Workflow Setup for FLUX\n")
    
    # 1. Check workflow file
    workflow_path = "runpod/src/workflows/flux_with_lora.json"
    if os.path.exists(workflow_path):
        print("✅ LoRA workflow file exists")
        
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
            
        # Check for LoRA node
        lora_node = None
        for node_id, node in workflow.items():
            if node.get("class_type") == "LoraLoaderModelOnly":
                lora_node = node
                break
        
        if lora_node:
            print("✅ LoRA node found in workflow")
            print(f"   - Node type: {lora_node['class_type']}")
            print(f"   - Default LoRA: {lora_node['inputs'].get('lora_name', 'Not set')}")
            print(f"   - Default strength: {lora_node['inputs'].get('strength_model', 'Not set')}")
            
            # Check connections
            model_input = lora_node['inputs'].get('model', [])
            if model_input and isinstance(model_input, list):
                print(f"   - Connected to model node: {model_input[0]}")
                
                # Find what's using the LoRA output
                for check_id, check_node in workflow.items():
                    if check_node.get("inputs", {}).get("model") == ["40", 0]:
                        print(f"   - LoRA output connected to: {check_node.get('class_type')} (node {check_id})")
        else:
            print("❌ No LoRA node found in workflow!")
    else:
        print("❌ LoRA workflow file not found!")
    
    print("\n📦 Checking Handler Implementation\n")
    
    # 2. Check handler
    handler_path = "runpod/src/flux_handler.py"
    if os.path.exists(handler_path):
        print("✅ Handler file exists")
        
        with open(handler_path, 'r') as f:
            handler_content = f.read()
            
        # Check for LoRA handling
        checks = [
            ("LoRA workflow loading", "elif lora_name:"),
            ("LoRA node update", 'node["inputs"]["lora_name"]'),
            ("LoRA strength update", 'node["inputs"]["strength_model"]'),
            ("Known LoRAs mapping", '"shiyuanlimei_v1.0"'),
            ("LoRA download logic", "urllib.request.urlretrieve")
        ]
        
        for check_name, check_string in checks:
            if check_string in handler_content:
                print(f"✅ {check_name} implemented")
            else:
                print(f"❌ {check_name} NOT found")
    
    print("\n🎨 Available LoRAs\n")
    print("Currently configured LoRA:")
    print("- shiyuanlimei_v1.0 (Anime style)")
    print("  Firebase URL: https://firebasestorage.googleapis.com/.../shiyuanlimei_v1.0.safetensors")
    
    print("\n📋 How to Test LoRA\n")
    print("1. In the web UI, select 'Shiyuanlimei v1.0' from the LoRA dropdown")
    print("2. Or use custom JSON:")
    print(json.dumps({
        "prompt": "anime girl with blue hair",
        "lora_name": "shiyuanlimei_v1.0",
        "lora_strength": 0.8,
        "width": 1024,
        "height": 1024
    }, indent=2))
    
    print("\n🔧 ComfyUI Workflow Structure\n")
    print("The LoRA implementation follows this flow:")
    print("1. UNETLoader (node 37) → Loads base FLUX model")
    print("2. LoraLoaderModelOnly (node 40) → Applies LoRA to model")
    print("3. KSampler (node 31) → Uses LoRA-modified model for generation")
    
    print("\n⚠️  Common Issues\n")
    print("1. LoRA file not found: Handler will auto-download on first use")
    print("2. Wrong filename: Must include .safetensors extension")
    print("3. Path issues: LoRA should be in /ComfyUI/models/loras/")

if __name__ == "__main__":
    check_lora_workflow()