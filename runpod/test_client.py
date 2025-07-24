#!/usr/bin/env python3
"""
Test client for RunPod simulation
Tests various timeout and error scenarios
"""

import requests
import json
import time
import sys

def test_scenario(scenario_name, timeout_seconds=360):
    """Test a specific scenario"""
    print(f"\n=== Testing {scenario_name} ===")
    
    # Set simulation mode
    # In real implementation, you'd restart the server with different SIMULATION_MODE
    
    url = "http://localhost:5000/runsync"
    
    payload = {
        "input": {
            "prompt": "test prompt for simulation",
            "width": 1024,
            "height": 1024
        }
    }
    
    start_time = time.time()
    print(f"Sending request at {time.strftime('%H:%M:%S')}")
    
    try:
        # Use timeout to simulate Firebase/client timeout
        response = requests.post(url, json=payload, timeout=timeout_seconds)
        elapsed = time.time() - start_time
        
        print(f"Response received after {elapsed:.1f}s")
        print(f"Status code: {response.status_code}")
        
        result = response.json()
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get('status') == 'COMPLETED':
            print("✅ Success!")
        else:
            print("❌ Failed!")
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"❌ Request timed out after {elapsed:.1f}s")
        print("This simulates what happens in Firebase Functions")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_all_scenarios():
    """Test all scenarios"""
    print("RunPod Simulation Test Suite")
    print("============================")
    
    scenarios = [
        ("normal", 180),      # Should complete in ~2 min
        ("slow", 240),        # Should complete in ~3 min  
        ("timeout", 60),      # Will timeout at client level
        ("error", 180),       # Should fail fast
        ("handler_error", 180),  # Should fail immediately
    ]
    
    for scenario, timeout in scenarios:
        test_scenario(scenario, timeout)
        time.sleep(2)  # Brief pause between tests

def test_firebase_timeout():
    """Simulate Firebase's 60s timeout"""
    print("\n=== Simulating Firebase 60s Timeout ===")
    print("This shows what happens when Firebase times out")
    test_scenario("slow", 60)  # 60 second timeout like old Firebase

def test_extended_timeout():
    """Simulate Firebase's 540s timeout"""
    print("\n=== Simulating Extended 540s Timeout ===")
    print("This shows behavior with extended timeout")
    test_scenario("slow", 540)

if __name__ == "__main__":
    print("Make sure simulate_runpod.py is running first!")
    print("Run: python simulate_runpod.py")
    input("\nPress Enter to start tests...")
    
    if len(sys.argv) > 1:
        # Test specific scenario
        test_scenario(sys.argv[1])
    else:
        # Test Firebase timeout scenarios
        test_firebase_timeout()
        test_extended_timeout()