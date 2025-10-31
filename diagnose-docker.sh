#!/bin/bash
# Docker diagnostic script to debug container hang issues

echo "=========================================="
echo "Workflow Tracker - Docker Diagnostics"
echo "=========================================="
echo ""

# Check if .env exists
echo "1. Checking .env file..."
if [ -f ".env" ]; then
    echo "   ✓ .env exists"
    echo "   Preview (credentials masked):"
    grep -v "API_TOKEN\|PASSWORD" .env | head -n 5 || echo "   (empty or unreadable)"
else
    echo "   ✗ .env NOT FOUND!"
    echo "   Run: cp .env.example .env"
    echo "   Then edit .env with your values"
fi
echo ""

# Check if config/local.yaml exists
echo "2. Checking config/local.yaml..."
if [ -f "config/local.yaml" ]; then
    echo "   ✓ config/local.yaml exists"
else
    echo "   ✗ config/local.yaml NOT FOUND!"
    echo "   Run: cp config/config.example.yaml config/local.yaml"
fi
echo ""

# Check Docker container status
echo "3. Checking Docker container status..."
if docker ps -a | grep -q workflow-tracker; then
    echo "   Container exists. Status:"
    docker ps -a --filter name=workflow-tracker --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "   No workflow-tracker container found"
fi
echo ""

# Check container logs
echo "4. Checking container logs (last 20 lines)..."
if docker ps -a | grep -q workflow-tracker; then
    docker logs workflow-tracker --tail 20 2>&1 || echo "   (no logs yet)"
else
    echo "   Container not running, no logs available"
fi
echo ""

# Check if config can be loaded
echo "5. Testing configuration loading..."
if [ -f ".env" ] && [ -f "config/local.yaml" ]; then
    docker run --rm \
        -v $(pwd)/config:/app/config:ro \
        --env-file .env \
        workflow-tracker:latest \
        python3 -c "
from src.config_loader import Config
try:
    cfg = Config('/app/config/local.yaml')
    print('   ✓ Configuration loads successfully')
    print(f'   Repository path: {cfg.get_repository_path()}')
    print(f'   Confluence URL: {cfg.get(\"confluence.url\", \"not set\")}')
except Exception as e:
    print(f'   ✗ Configuration error: {e}')
" 2>&1
else
    echo "   Skipping (missing .env or config/local.yaml)"
fi
echo ""

# Recommendations
echo "=========================================="
echo "Recommendations:"
echo "=========================================="

if [ ! -f ".env" ]; then
    echo "⚠️  Create .env file:"
    echo "   cp .env.example .env"
    echo "   Edit .env with your values"
    echo ""
fi

if [ ! -f "config/local.yaml" ]; then
    echo "⚠️  Create config/local.yaml:"
    echo "   cp config/config.example.yaml config/local.yaml"
    echo ""
fi

echo "To view real-time logs:"
echo "   docker logs -f workflow-tracker"
echo ""
echo "To check if container is hanging on config:"
echo "   docker exec -it workflow-tracker /bin/bash"
echo ""
echo "To restart with verbose output:"
echo "   docker-compose down"
echo "   docker-compose up --build"
echo ""
