#!/usr/bin/env python3
"""Simple test to check workflow files"""

import json
import os

# Check workflow files
workflow_dir = "src/workflows"
print(f"Checking workflows in {workflow_dir}...\n")

workflows = {
    "flux_actual.json": "Standard FLUX workflow",
    "flux_with_lora.json": "FLUX with LoRA workflow"
}

for filename, description in workflows.items():
    filepath = os.path.join(workflow_dir, filename)
    if os.path.exists(filepath):
        print(f"✓ {filename} - {description}")
        with open(filepath, 'r') as f:
            workflow = json.load(f)
            print(f"  Nodes: {len(workflow)}")
            
            # Check for LoRA nodes
            lora_nodes = []
            for node_id, node in workflow.items():
                if node.get("class_type") in ["LoraLoader", "LoraLoaderModelOnly"]:
                    lora_nodes.append(node_id)
                    
            if lora_nodes:
                print(f"  LoRA nodes: {lora_nodes}")
                for node_id in lora_nodes:
                    node = workflow[node_id]
                    print(f"    Node {node_id}: {node['inputs'].get('lora_name', 'No default')}")
            else:
                print("  No LoRA nodes")
                
            # Check what connects to KSampler
            for node_id, node in workflow.items():
                if node.get("class_type") == "KSampler":
                    model_input = node["inputs"].get("model", [None, None])
                    print(f"  KSampler gets model from node: {model_input[0]}")
                    
            print()
    else:
        print(f"✗ {filename} - NOT FOUND")

# Show the key difference
print("\nKey difference:")
print("- flux_actual.json: KSampler uses model directly from UNETLoader")
print("- flux_with_lora.json: KSampler uses model from LoRA loader (which gets it from UNETLoader)")