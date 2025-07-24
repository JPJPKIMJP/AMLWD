#!/bin/bash
# Emergency Rollback Script
# Quickly rollback to last known working state

set -e

echo "🔄 RunPod Emergency Rollback"
echo "==========================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Show recent commits
echo "Recent commits:"
git log --oneline -10

echo
read -p "Enter commit hash to rollback to (or 'cancel'): " commit_hash

if [ "$commit_hash" == "cancel" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Verify commit exists
if ! git rev-parse --quiet --verify $commit_hash > /dev/null; then
    echo -e "${RED}Invalid commit hash${NC}"
    exit 1
fi

echo
echo -e "${YELLOW}Rolling back to:${NC}"
git log --oneline -1 $commit_hash

echo
read -p "Are you sure? This will reset to this commit. (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create backup branch
    backup_branch="backup-$(date +%Y%m%d-%H%M%S)"
    git branch $backup_branch
    echo -e "${GREEN}Created backup branch: $backup_branch${NC}"
    
    # Reset to commit
    git reset --hard $commit_hash
    echo -e "${GREEN}Reset to commit $commit_hash${NC}"
    
    # Push to remote (force)
    echo "Pushing to remote..."
    git push --force origin main
    
    echo
    echo -e "${GREEN}✓ Rollback complete!${NC}"
    echo
    echo "Next steps:"
    echo "1. Update RunPod to use previous Docker image if needed"
    echo "2. Redeploy Firebase functions: firebase deploy --only functions"
    echo "3. Monitor for stability"
    echo
    echo "To restore the backup:"
    echo "git checkout $backup_branch"
else
    echo "Rollback cancelled"
fi