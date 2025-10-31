#!/bin/bash
# Quick setup script for Docker deployment

set -e

echo "=========================================="
echo "Workflow Tracker - Docker Setup"
echo "=========================================="
echo ""

# Check if config/local.yaml exists
if [ -f "config/local.yaml" ]; then
    echo "✓ config/local.yaml already exists"
else
    echo "Creating config/local.yaml from template..."
    cp config/config.example.yaml config/local.yaml
    echo "✓ Created config/local.yaml"
    echo ""
    echo "⚠️  IMPORTANT: You must edit config/local.yaml with your settings!"
    echo "   - Set your repository path"
    echo "   - Add Confluence credentials"
    echo "   - Verify exclusions (node_modules, bin, obj, etc.)"
    echo ""
fi

# Check if .env exists
if [ -f ".env" ]; then
    echo "✓ .env already exists"
else
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✓ Created .env"
    echo ""
    echo "⚠️  IMPORTANT: You must edit .env with your settings!"
    echo "   - Set REPO_TO_SCAN to your repository path"
    echo "   - Add Confluence credentials (URL, username, API token, space key)"
    echo ""
fi

# Check if config is properly configured
if grep -q "your-domain.atlassian.net" config/local.yaml 2>/dev/null; then
    echo ""
    echo "⚠️  WARNING: config/local.yaml still has default values!"
    echo "   Edit config/local.yaml before running docker-compose"
    echo ""
fi

if grep -q "/path/to/your/repo" .env 2>/dev/null; then
    echo ""
    echo "⚠️  WARNING: .env still has default values!"
    echo "   Edit .env before running docker-compose"
    echo ""
fi

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config/local.yaml with your settings"
echo "2. Edit .env with your repository path and Confluence credentials"
echo "3. Run: docker-compose up workflow-tracker"
echo ""
echo "The config file is CRITICAL for performance!"
echo "It excludes node_modules, bin, obj, etc."
echo "Without it, scans will take much longer!"
echo ""
