#!/bin/bash
# RunPod Deployment Monitoring Script
# Helps monitor and troubleshoot deployments

set -e

echo "🔍 RunPod Deployment Monitor"
echo "==========================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if environment variables are set
check_env() {
    if [ -z "$RUNPOD_API_KEY" ]; then
        echo -e "${RED}Error: RUNPOD_API_KEY not set${NC}"
        echo "Export it with: export RUNPOD_API_KEY=your_key"
        exit 1
    fi
    
    if [ -z "$RUNPOD_ENDPOINT_ID" ]; then
        echo -e "${RED}Error: RUNPOD_ENDPOINT_ID not set${NC}"
        echo "Export it with: export RUNPOD_ENDPOINT_ID=your_endpoint_id"
        exit 1
    fi
}

# Function to check endpoint status
check_endpoint() {
    echo -e "\n${BLUE}Checking endpoint status...${NC}"
    
    response=$(curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
        "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID")
    
    if [ $? -eq 0 ]; then
        echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Endpoint ID: {data.get(\"id\", \"Unknown\")}')
print(f'Name: {data.get(\"name\", \"Unknown\")}')
print(f'Status: {data.get(\"status\", \"Unknown\")}')
print(f'GPU: {data.get(\"gpuType\", \"Unknown\")}')
print(f'Workers: {data.get(\"workerCount\", 0)}')
"
    else
        echo -e "${RED}Failed to get endpoint status${NC}"
    fi
}

# Function to check workers
check_workers() {
    echo -e "\n${BLUE}Checking workers...${NC}"
    
    response=$(curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
        "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/workers")
    
    if [ $? -eq 0 ]; then
        echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
workers = data.get('workers', [])
if not workers:
    print('No active workers')
else:
    for w in workers:
        print(f\"Worker {w.get('id', 'Unknown')}: {w.get('status', 'Unknown')}\")
"
    else
        echo -e "${RED}Failed to get worker status${NC}"
    fi
}

# Function to test with minimal request
test_minimal() {
    echo -e "\n${BLUE}Testing with minimal request...${NC}"
    
    response=$(curl -s -X POST "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/runsync" \
        -H "Authorization: Bearer $RUNPOD_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "input": {
                "prompt": "test",
                "width": 512,
                "height": 512
            }
        }')
    
    echo "$response" | python3 -m json.tool || echo "$response"
}

# Function to get recent logs
get_logs() {
    echo -e "\n${BLUE}Recent logs (if available)...${NC}"
    
    # Get worker IDs
    workers=$(curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
        "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/workers" | \
        python3 -c "import json, sys; print(' '.join([w['id'] for w in json.load(sys.stdin).get('workers', [])]))" 2>/dev/null)
    
    if [ -n "$workers" ]; then
        for worker in $workers; do
            echo -e "\n${YELLOW}Logs for worker $worker:${NC}"
            echo "Run: runpod logs $worker -f"
        done
    else
        echo "No active workers found"
    fi
}

# Function to check model loading
check_model_status() {
    echo -e "\n${BLUE}Checking model status...${NC}"
    
    cat << 'EOF' > check_model.py
import requests
import json

# Test if models are accessible
test_payload = {
    "input": {
        "test_mode": True
    }
}

print("This would check if models are loaded...")
print("Run a test generation to see actual model loading")
EOF
    
    python3 check_model.py
    rm check_model.py
}

# Main menu
show_menu() {
    echo -e "\n${GREEN}Available commands:${NC}"
    echo "1) Check endpoint status"
    echo "2) Check workers"
    echo "3) Test minimal request"
    echo "4) Get worker logs info"
    echo "5) Continuous monitoring (Ctrl+C to stop)"
    echo "6) Check model status"
    echo "7) Full diagnostic"
    echo "q) Quit"
}

# Continuous monitoring
continuous_monitor() {
    echo -e "${YELLOW}Starting continuous monitoring... (Ctrl+C to stop)${NC}"
    
    while true; do
        clear
        echo "RunPod Monitor - $(date)"
        echo "=================="
        check_endpoint
        check_workers
        sleep 5
    done
}

# Full diagnostic
full_diagnostic() {
    echo -e "\n${YELLOW}Running full diagnostic...${NC}"
    
    check_endpoint
    check_workers
    
    echo -e "\n${BLUE}Environment check:${NC}"
    echo "RUNPOD_API_KEY: ${RUNPOD_API_KEY:0:10}..."
    echo "RUNPOD_ENDPOINT_ID: $RUNPOD_ENDPOINT_ID"
    
    echo -e "\n${BLUE}Testing connection:${NC}"
    curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
        -H "Authorization: Bearer $RUNPOD_API_KEY" \
        "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID"
    
    get_logs
}

# Main script
check_env

if [ "$1" == "--continuous" ] || [ "$1" == "-c" ]; then
    continuous_monitor
elif [ "$1" == "--diagnostic" ] || [ "$1" == "-d" ]; then
    full_diagnostic
else
    while true; do
        show_menu
        read -p "Select option: " choice
        
        case $choice in
            1) check_endpoint ;;
            2) check_workers ;;
            3) test_minimal ;;
            4) get_logs ;;
            5) continuous_monitor ;;
            6) check_model_status ;;
            7) full_diagnostic ;;
            q|Q) exit 0 ;;
            *) echo -e "${RED}Invalid option${NC}" ;;
        esac
    done
fi