#!/bin/bash
# RunPod Deployment Script
# Automates the deployment process with safety checks

set -e  # Exit on error

echo "🚀 RunPod FLUX Deployment Script"
echo "================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="jpjpkimjp/flux-comfyui"
DOCKER_TAG="latest"
GITHUB_REPO="https://github.com/JPJPKIMJP/AMLWD.git"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Pre-flight checks
echo "Running pre-flight checks..."
echo

# Check for required tools
if ! command_exists python3; then
    print_error "Python3 not found. Please install Python 3."
    exit 1
fi

if ! command_exists git; then
    print_error "Git not found. Please install Git."
    exit 1
fi

if ! command_exists docker; then
    print_warning "Docker not found. Will use GitHub Actions for building."
fi

# Run validation tests
echo "1. Running validation tests..."
if python3 test_before_deploy.py > /dev/null 2>&1; then
    print_status "Pre-deployment tests passed"
else
    print_error "Pre-deployment tests failed. Run 'python3 test_before_deploy.py' for details."
    exit 1
fi

if python3 validate_workflows.py > /dev/null 2>&1; then
    print_status "Workflow validation passed"
else
    print_error "Workflow validation failed. Run 'python3 validate_workflows.py' for details."
    exit 1
fi

echo
echo "2. Checking Git status..."

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    print_warning "You have uncommitted changes:"
    git status -s
    echo
    read -p "Do you want to commit these changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " commit_msg
        git add -A
        git commit -m "$commit_msg

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
        print_status "Changes committed"
    else
        print_warning "Proceeding with uncommitted changes"
    fi
else
    print_status "No uncommitted changes"
fi

echo
echo "3. Docker image options:"
echo "   a) Build locally and push (requires Docker)"
echo "   b) Push to GitHub and use Actions (recommended)"
echo "   c) Skip image build (use existing)"
echo
read -p "Choose option (a/b/c): " -n 1 -r build_option
echo

case $build_option in
    a|A)
        if ! command_exists docker; then
            print_error "Docker not installed. Use option 'b' instead."
            exit 1
        fi
        
        echo "Building Docker image locally..."
        
        # Increment version
        VERSION=$(date +%Y%m%d-%H%M%S)
        FULL_TAG="${DOCKER_IMAGE}:${VERSION}"
        
        # Build image
        docker build -f Dockerfile.flux -t $FULL_TAG .
        
        if [ $? -eq 0 ]; then
            print_status "Docker image built: $FULL_TAG"
            
            # Push to registry
            echo "Pushing to Docker Hub..."
            docker push $FULL_TAG
            docker tag $FULL_TAG ${DOCKER_IMAGE}:latest
            docker push ${DOCKER_IMAGE}:latest
            
            print_status "Image pushed to registry"
        else
            print_error "Docker build failed"
            exit 1
        fi
        ;;
        
    b|B)
        echo "Pushing to GitHub for Actions build..."
        
        # Push to GitHub
        git push origin main
        
        print_status "Pushed to GitHub"
        echo
        echo "GitHub Actions will build and push the Docker image."
        echo "Monitor progress at: https://github.com/JPJPKIMJP/AMLWD/actions"
        echo
        echo "Wait for the build to complete before proceeding."
        read -p "Press Enter when the build is complete..."
        ;;
        
    c|C)
        print_warning "Using existing Docker image"
        ;;
        
    *)
        print_error "Invalid option"
        exit 1
        ;;
esac

echo
echo "4. RunPod Deployment Steps:"
echo

cat << 'EOF'
📋 Manual steps required in RunPod dashboard:

1. Go to RunPod Serverless
   https://www.runpod.ai/console/serverless

2. Find your FLUX endpoint

3. Update the Docker image:
   - Click "Manage" on your endpoint
   - Update container image to: jpjpkimjp/flux-comfyui:latest
   - Click "Save"

4. Verify environment variables:
   ✓ R2_ENDPOINT
   ✓ R2_ACCESS_KEY_ID  
   ✓ R2_SECRET_ACCESS_KEY
   ✓ R2_BUCKET
   ✓ R2_PUBLIC_URL

5. Worker configuration:
   - Active workers: 0 (scale to 1 for testing)
   - Max workers: 3
   - GPU: 24GB minimum
   - Idle timeout: 60 seconds

6. Scale workers:
   - Set active workers to 1
   - Wait for worker to become ready

EOF

echo
read -p "Have you completed the RunPod configuration? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Complete RunPod configuration before testing"
    exit 0
fi

echo
echo "5. Quick Test Commands:"
echo

cat << 'EOF' > test_deployment.sh
#!/bin/bash
# Test the deployment

echo "Testing FLUX deployment..."

# Simple test with small dimensions
curl -X POST https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "a simple red circle on white background",
      "width": 512,
      "height": 512
    }
  }' | python3 -m json.tool

EOF

chmod +x test_deployment.sh

print_status "Created test_deployment.sh"

echo
echo "6. Monitoring Commands:"
echo

cat << 'EOF'
# View RunPod logs
runpod logs <worker-id> -f

# Check Firebase function logs  
firebase functions:log --only generateImageSecure -n 50

# Monitor worker status
watch -n 5 'curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/workers'

EOF

echo
echo "✅ Deployment preparation complete!"
echo
echo "Next steps:"
echo "1. Ensure RunPod workers are scaled up"
echo "2. Run ./test_deployment.sh to test"
echo "3. Try generating an image from the web app"
echo
print_warning "Remember: First generation will be slow due to model loading"