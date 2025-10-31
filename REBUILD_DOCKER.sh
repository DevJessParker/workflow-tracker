#!/bin/bash
# Script to rebuild Docker image with latest fixes

echo "=== Workflow Tracker - Rebuild Script ==="
echo ""

# Stop any running containers
echo "1. Stopping existing containers..."
docker-compose down

# Pull latest changes (if needed)
echo ""
echo "2. Checking for latest code..."
git pull origin claude/scan-data-workflows-011CUeBpfcn7LqhQHwoFjDNf

# Remove old image to force rebuild
echo ""
echo "3. Removing old Docker image..."
docker rmi workflow-tracker:latest 2>/dev/null || echo "   No old image to remove"

# Build new image
echo ""
echo "4. Building new Docker image with latest fixes..."
docker build --no-cache -t workflow-tracker .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Docker image rebuilt successfully!"
    echo ""
    echo "To verify the fixes are included, run:"
    echo "  docker run --rm workflow-tracker pip list | grep scipy"
    echo ""
    echo "You should see: scipy 1.11.4"
    echo ""
    echo "To run the scan:"
    echo "  docker-compose up workflow-tracker"
else
    echo ""
    echo "✗ Build failed. Check errors above."
    exit 1
fi
