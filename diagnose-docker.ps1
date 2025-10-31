# Docker diagnostic script to debug container hang issues

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Workflow Tracker - Docker Diagnostics" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
Write-Host "1. Checking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   OK .env exists" -ForegroundColor Green
    Write-Host "   Preview (credentials masked):"
    Get-Content .env | Where-Object { $_ -notmatch "API_TOKEN|PASSWORD" } | Select-Object -First 5
} else {
    Write-Host "   ERROR .env NOT FOUND!" -ForegroundColor Red
    Write-Host "   Run: cp .env.example .env"
    Write-Host "   Then edit .env with your values"
}
Write-Host ""

# Check if config/local.yaml exists
Write-Host "2. Checking config/local.yaml..." -ForegroundColor Yellow
if (Test-Path "config/local.yaml") {
    Write-Host "   OK config/local.yaml exists" -ForegroundColor Green
} else {
    Write-Host "   ERROR config/local.yaml NOT FOUND!" -ForegroundColor Red
    Write-Host "   Run: cp config/config.example.yaml config/local.yaml"
}
Write-Host ""

# Check Docker container status
Write-Host "3. Checking Docker container status..." -ForegroundColor Yellow
$container = docker ps -a --filter name=workflow-tracker --format "{{.Names}}" 2>$null
if ($container) {
    Write-Host "   Container exists. Status:"
    docker ps -a --filter name=workflow-tracker --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
} else {
    Write-Host "   No workflow-tracker container found"
}
Write-Host ""

# Check container logs
Write-Host "4. Checking container logs (last 20 lines)..." -ForegroundColor Yellow
if ($container) {
    docker logs workflow-tracker --tail 20 2>&1
} else {
    Write-Host "   Container not running, no logs available"
}
Write-Host ""

# Recommendations
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Recommendations:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "WARNING: Create .env file:" -ForegroundColor Yellow
    Write-Host "   Copy-Item .env.example .env"
    Write-Host "   Edit .env with your values"
}

if (-not (Test-Path "config/local.yaml")) {
    Write-Host ""
    Write-Host "WARNING: Create config/local.yaml:" -ForegroundColor Yellow
    Write-Host "   Copy-Item config/config.example.yaml config/local.yaml"
}

Write-Host ""
Write-Host "To view real-time logs:"
Write-Host "   docker logs -f workflow-tracker"
Write-Host ""
Write-Host "To check inside container:"
Write-Host "   docker exec -it workflow-tracker /bin/bash"
Write-Host ""
Write-Host "To restart with verbose output:"
Write-Host "   docker-compose down"
Write-Host "   docker-compose up --build"
Write-Host ""
