#!/usr/bin/env python3
"""
Validate FLUX workflows without requiring RunPod environment
"""

import json
import sys

def validate_workflow(filepath):
    """Validate a single workflow file"""
    print(f"\n=== Validating {filepath} ===")
    
    try:
        with open(filepath, 'r') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return False
        
    issues = []
    warnings = []
    
    # Check each node
    for node_id, node in workflow.items():
        node_class = node.get('class_type', 'Unknown')
        node_title = node.get('_meta', {}).get('title', f'Node {node_id}')
        
        print(f"\nNode {node_id} ({node_class}): {node_title}")
        
        # Check inputs exist
        if 'inputs' not in node:
            issues.append(f"Node {node_id} missing 'inputs'")
            continue
            
        inputs = node['inputs']
        
        # Node-specific validation
        if node_class == 'KSampler':
            # Check seed
            seed = inputs.get('seed', None)
            if seed is None:
                issues.append(f"KSampler missing seed")
            elif seed < 0:
                issues.append(f"KSampler seed is {seed}, must be >= 0")
            else:
                print(f"  ✓ Seed: {seed}")
                
            # Check other required parameters
            required = ['steps', 'cfg', 'sampler_name', 'scheduler', 'denoise']
            for param in required:
                if param in inputs:
                    print(f"  ✓ {param}: {inputs[param]}")
                else:
                    issues.append(f"KSampler missing {param}")
                    
        elif node_class == 'UNETLoader':
            unet_name = inputs.get('unet_name', '')
            if 'REPLACE' in unet_name.upper():
                issues.append(f"UNETLoader has placeholder: {unet_name}")
            else:
                print(f"  ✓ Model: {unet_name}")
                
        elif node_class == 'CheckpointLoaderSimple':
            ckpt_name = inputs.get('ckpt_name', '')
            if 'REPLACE' in ckpt_name.upper():
                issues.append(f"CheckpointLoader has placeholder: {ckpt_name}")
            else:
                print(f"  ✓ Checkpoint: {ckpt_name}")
                
        elif node_class == 'DualCLIPLoader':
            clip1 = inputs.get('clip_name1', '')
            clip2 = inputs.get('clip_name2', '')
            print(f"  ✓ CLIP1: {clip1}")
            print(f"  ✓ CLIP2: {clip2}")
            
        elif node_class == 'VAELoader':
            vae = inputs.get('vae_name', '')
            print(f"  ✓ VAE: {vae}")
            
        elif node_class == 'EmptyLatentImage':
            width = inputs.get('width', 1024)
            height = inputs.get('height', 1024)
            print(f"  ✓ Dimensions: {width}x{height}")
            if width > 1024 or height > 1024:
                warnings.append(f"Large dimensions ({width}x{height}) will be slow")
                
        elif node_class == 'CLIPTextEncode':
            text = inputs.get('text', '')
            print(f"  ✓ Text: '{text[:50]}...'")
            
        # Check node connections
        for input_name, input_value in inputs.items():
            if isinstance(input_value, list) and len(input_value) == 2:
                ref_node_id = str(input_value[0])
                ref_output = input_value[1]
                if ref_node_id not in workflow:
                    issues.append(f"Node {node_id} references non-existent node {ref_node_id}")
                else:
                    print(f"  ✓ {input_name} connected to node {ref_node_id}[{ref_output}]")
    
    # Summary
    print(f"\n=== Summary for {filepath} ===")
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No critical issues found")
        
    if warnings:
        print(f"⚠️  {len(warnings)} warnings:")
        for warning in warnings:
            print(f"  - {warning}")
            
    return len(issues) == 0

def main():
    """Validate all workflows"""
    print("FLUX Workflow Validation")
    print("========================")
    
    workflows = [
        "src/workflows/flux_actual.json",
        "src/workflows/flux_img2img.json"
    ]
    
    all_valid = True
    for workflow in workflows:
        if not validate_workflow(workflow):
            all_valid = False
            
    print("\n========================")
    if all_valid:
        print("✅ All workflows are valid!")
        return 0
    else:
        print("❌ Some workflows have issues that need fixing")
        return 1

if __name__ == "__main__":
    sys.exit(main())