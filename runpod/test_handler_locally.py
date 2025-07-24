#!/usr/bin/env python3
"""
Test FLUX handler locally without deploying to RunPod
This helps catch issues before deployment
"""

import sys
import os
import json
import time
import importlib.util

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_handler():
    """Load the handler module"""
    spec = importlib.util.spec_from_file_location("flux_handler", "src/flux_handler.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_handler_locally():
    """Test handler without RunPod"""
    print("Testing FLUX Handler Locally")
    print("============================\n")
    
    # Mock RunPod environment
    os.environ['RUNPOD_POD_ID'] = 'test-local'
    
    # Load handler
    try:
        handler_module = load_handler()
        print("✓ Handler loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load handler: {e}")
        return
    
    # Test 1: Check workflow loading
    print("\n--- Test 1: Workflow Loading ---")
    try:
        handler = handler_module.FluxHandler()
        workflow = handler.load_workflow(is_img2img=False)
        print("✓ Text-to-image workflow loaded")
        
        # Check for common issues
        has_negative_seed = False
        for node in workflow.values():
            if node.get('class_type') == 'KSampler':
                seed = node['inputs'].get('seed', 0)
                if seed < 0:
                    print(f"✗ ERROR: Negative seed found: {seed}")
                    has_negative_seed = True
                    
        if not has_negative_seed:
            print("✓ No negative seed issues")
            
    except Exception as e:
        print(f"✗ Workflow loading failed: {e}")
        
    # Test 2: Prompt update
    print("\n--- Test 2: Prompt Update ---")
    try:
        test_prompt = "a beautiful test landscape"
        updated_workflow = handler.update_prompt(workflow, test_prompt, 512, 512)
        
        # Verify prompt was updated
        prompt_found = False
        for node in updated_workflow.values():
            if node.get('class_type') in ['CLIPTextEncode', 'CLIPTextEncodeFlux']:
                if node['inputs'].get('text') == test_prompt:
                    prompt_found = True
                    print(f"✓ Prompt updated correctly")
                    
        if not prompt_found:
            print("✗ Prompt not found in workflow")
            
        # Check seed was randomized
        for node in updated_workflow.values():
            if node.get('class_type') == 'KSampler':
                seed = node['inputs'].get('seed', 0)
                if seed > 0:
                    print(f"✓ Seed randomized: {seed}")
                else:
                    print(f"✗ Seed not randomized: {seed}")
                    
    except Exception as e:
        print(f"✗ Prompt update failed: {e}")
        
    # Test 3: Simulate RunPod job
    print("\n--- Test 3: Handler Execution ---")
    test_job = {
        "id": "test-job-123",
        "input": {
            "prompt": "test prompt",
            "width": 512,
            "height": 512
        }
    }
    
    print("Would execute handler with job:")
    print(json.dumps(test_job, indent=2))
    
    # Test 4: Check timeouts
    print("\n--- Test 4: Timeout Configuration ---")
    print(f"Handler timeout: {handler.wait_for_image.__defaults__[0]}s")
    if handler.wait_for_image.__defaults__[0] >= 300:
        print("✓ Timeout is sufficient for FLUX (>= 300s)")
    else:
        print("✗ Timeout may be too short for FLUX")

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("\n--- Prerequisites Check ---")
    
    # Check workflow files
    workflows = [
        "src/workflows/flux_actual.json",
        "src/workflows/flux_img2img.json"
    ]
    
    for wf in workflows:
        if os.path.exists(wf):
            print(f"✓ {wf} exists")
            # Check if valid JSON
            try:
                with open(wf) as f:
                    json.load(f)
                print(f"  ✓ Valid JSON")
            except:
                print(f"  ✗ Invalid JSON!")
        else:
            print(f"✗ {wf} missing!")
            
    # Check environment variables
    print("\n--- Environment Variables ---")
    env_vars = ['R2_ENDPOINT', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET']
    
    for var in env_vars:
        if os.environ.get(var):
            print(f"✓ {var} is set")
        else:
            print(f"⚠️  {var} not set (R2 will not work)")

if __name__ == "__main__":
    check_prerequisites()
    test_handler_locally()