#!/usr/bin/env python3
"""Test script to verify LoRA workflow loading"""

import json
import sys
sys.path.append('src')

from flux_handler import FluxHandler

# Initialize handler
handler = FluxHandler()

# Test loading workflows
print("Testing workflow loading...\n")

# Test 1: Load standard workflow
print("1. Loading standard workflow (no LoRA):")
try:
    workflow = handler.load_workflow(is_img2img=False, lora_name=None)
    print(f"✓ Success - Loaded {len(workflow)} nodes")
    has_lora = any(node.get("class_type") in ["LoraLoader", "LoraLoaderModelOnly"] for node in workflow.values())
    print(f"  Has LoRA nodes: {has_lora}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n2. Loading LoRA workflow:")
try:
    workflow = handler.load_workflow(is_img2img=False, lora_name="mix4")
    print(f"✓ Success - Loaded {len(workflow)} nodes")
    has_lora = any(node.get("class_type") in ["LoraLoader", "LoraLoaderModelOnly"] for node in workflow.values())
    print(f"  Has LoRA nodes: {has_lora}")
    
    # Check LoRA node details
    for node_id, node in workflow.items():
        if node.get("class_type") == "LoraLoaderModelOnly":
            print(f"  LoRA node {node_id}:")
            print(f"    - Default LoRA: {node['inputs'].get('lora_name')}")
            print(f"    - Model input: {node['inputs'].get('model')}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n3. Testing update_prompt with LoRA:")
try:
    workflow = handler.load_workflow(is_img2img=False, lora_name="mix4")
    updated_workflow = handler.update_prompt(
        workflow, 
        "test prompt", 
        lora_name="mix4",
        lora_strength=0.8
    )
    
    # Check if LoRA was updated
    for node_id, node in updated_workflow.items():
        if node.get("class_type") == "LoraLoaderModelOnly":
            print(f"✓ LoRA node {node_id} updated:")
            print(f"    - LoRA name: {node['inputs'].get('lora_name')}")
            print(f"    - Strength: {node['inputs'].get('strength_model')}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\nWorkflow paths being checked:")
import os
workflow_paths = [
    "/workflows/",
    "/src/workflows/",
    "/app/workflows/",
    "./workflows/",
    "workflows/",
    "src/workflows/"
]
for path in workflow_paths:
    if os.path.exists(path):
        print(f"  ✓ {path} exists")
        if os.path.exists(os.path.join(path, "flux_with_lora.json")):
            print(f"    → flux_with_lora.json found!")
    else:
        print(f"  ✗ {path} not found")