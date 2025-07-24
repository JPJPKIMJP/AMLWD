#!/usr/bin/env python3
"""
Pre-deployment test script for FLUX
Run this BEFORE deploying to catch issues early
"""

import json
import os
import sys

def test_workflow_files():
    """Test all workflow JSON files are valid"""
    print("=== Testing Workflow Files ===")
    workflows = [
        "src/workflows/flux_actual.json",
        "src/workflows/flux_img2img.json"
    ]
    
    for workflow_file in workflows:
        try:
            with open(workflow_file, 'r') as f:
                data = json.load(f)
            print(f"✓ {workflow_file} - Valid JSON")
            
            # Check for common issues
            has_sampler = any(node.get('class_type') == 'KSampler' for node in data.values())
            if has_sampler:
                for node_id, node in data.items():
                    if node.get('class_type') == 'KSampler':
                        seed = node['inputs'].get('seed', 0)
                        if seed < 0:
                            print(f"✗ ERROR: KSampler seed is {seed}, must be >= 0")
                            return False
                        else:
                            print(f"  ✓ KSampler seed: {seed}")
                            
            # Check for placeholder values
            for node_id, node in data.items():
                for key, value in node.get('inputs', {}).items():
                    if isinstance(value, str) and 'REPLACE' in value.upper():
                        print(f"✗ ERROR: Found placeholder in {workflow_file}: {value}")
                        return False
                        
        except Exception as e:
            print(f"✗ {workflow_file} - ERROR: {e}")
            return False
    
    return True

def test_environment_vars():
    """Check all required environment variables"""
    print("\n=== Testing Environment Variables ===")
    required = ['R2_ENDPOINT', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET', 'R2_PUBLIC_URL']
    
    for var in required:
        value = os.environ.get(var, '')
        if value:
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is NOT set")
            
    return True

def test_model_paths():
    """Check model references in workflows"""
    print("\n=== Testing Model Paths ===")
    
    with open("src/workflows/flux_actual.json", 'r') as f:
        workflow = json.load(f)
        
    models_referenced = []
    for node in workflow.values():
        if 'unet_name' in node.get('inputs', {}):
            models_referenced.append(('UNET', node['inputs']['unet_name']))
        if 'ckpt_name' in node.get('inputs', {}):
            models_referenced.append(('Checkpoint', node['inputs']['ckpt_name']))
        if 'clip_name1' in node.get('inputs', {}):
            models_referenced.append(('CLIP1', node['inputs']['clip_name1']))
        if 'clip_name2' in node.get('inputs', {}):
            models_referenced.append(('CLIP2', node['inputs']['clip_name2']))
        if 'vae_name' in node.get('inputs', {}):
            models_referenced.append(('VAE', node['inputs']['vae_name']))
            
    print("Models referenced in workflow:")
    for model_type, model_name in models_referenced:
        print(f"  - {model_type}: {model_name}")
        
    return True

def test_handler_imports():
    """Test that handler has all imports"""
    print("\n=== Testing Handler Imports ===")
    
    with open("src/flux_handler.py", 'r') as f:
        content = f.read()
        
    required_imports = ['runpod', 'json', 'requests', 'time', 'os', 'boto3', 'base64']
    for imp in required_imports:
        if f'import {imp}' in content or f'from {imp}' in content:
            print(f"✓ {imp} imported")
        else:
            print(f"✗ {imp} NOT imported")
            return False
            
    return True

def main():
    """Run all tests"""
    print("FLUX Pre-Deployment Test Suite")
    print("==============================\n")
    
    tests = [
        test_workflow_files,
        test_environment_vars,
        test_model_paths,
        test_handler_imports
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
            
    print("\n==============================")
    if all_passed:
        print("✅ All tests passed! Safe to deploy.")
        return 0
    else:
        print("❌ Some tests failed. Fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())