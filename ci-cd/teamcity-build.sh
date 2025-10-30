#!/bin/bash
# TeamCity Build Script for Workflow Tracker

set -e

echo "=== Workflow Tracker - TeamCity Integration ==="

# Build Docker image
echo "Building Docker image..."
docker build -t workflow-tracker:latest .

# Run workflow scan
echo "Scanning repository..."
docker run --rm \
  -v "${PWD}:/repo:ro" \
  -v "${PWD}/output:/app/output" \
  -e CONFLUENCE_URL="${CONFLUENCE_URL}" \
  -e CONFLUENCE_USERNAME="${CONFLUENCE_USERNAME}" \
  -e CONFLUENCE_API_TOKEN="${CONFLUENCE_API_TOKEN}" \
  -e CONFLUENCE_SPACE_KEY="${CONFLUENCE_SPACE_KEY}" \
  -e CI_MODE=true \
  workflow-tracker:latest \
  scan --repo /repo --publish

echo "✓ Workflow documentation updated successfully!"

# Optionally, publish artifacts to TeamCity
if [ -d "output" ]; then
  echo "##teamcity[publishArtifacts 'output/** => workflow-docs.zip']"
fi
