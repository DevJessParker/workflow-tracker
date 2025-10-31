# Quick setup script for Docker deployment (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Workflow Tracker - Docker Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if config/local.yaml exists
if (Test-Path "config/local.yaml") {
    Write-Host "OK config/local.yaml already exists" -ForegroundColor Green
} else {
    Write-Host "Creating config/local.yaml from template..." -ForegroundColor Yellow
    Copy-Item "config/config.example.yaml" "config/local.yaml"
    Write-Host "OK Created config/local.yaml" -ForegroundColor Green
    Write-Host ""
    Write-Host "WARNING: You must edit config/local.yaml with your settings!" -ForegroundColor Yellow
    Write-Host "   - Set your repository path"
    Write-Host "   - Add Confluence credentials"
    Write-Host "   - Verify exclusions (node_modules, bin, obj, etc.)"
    Write-Host ""
}

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "OK .env already exists" -ForegroundColor Green
} else {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "OK Created .env" -ForegroundColor Green
    Write-Host ""
    Write-Host "WARNING: You must edit .env with your settings!" -ForegroundColor Yellow
    Write-Host "   - Set REPO_TO_SCAN to your repository path"
    Write-Host "   - Add Confluence credentials (URL, username, API token, space key)"
    Write-Host ""
}

# Check if config is properly configured
$configContent = Get-Content "config/local.yaml" -Raw -ErrorAction SilentlyContinue
if ($configContent -and $configContent -match "your-domain.atlassian.net") {
    Write-Host ""
    Write-Host "WARNING: config/local.yaml still has default values!" -ForegroundColor Yellow
    Write-Host "   Edit config/local.yaml before running docker-compose"
    Write-Host ""
}

$envContent = Get-Content ".env" -Raw -ErrorAction SilentlyContinue
if ($envContent -and $envContent -match "/path/to/your/repo") {
    Write-Host ""
    Write-Host "WARNING: .env still has default values!" -ForegroundColor Yellow
    Write-Host "   Edit .env before running docker-compose"
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit config/local.yaml with your settings"
Write-Host "2. Edit .env with your repository path and Confluence credentials"
Write-Host "3. Run: docker-compose up workflow-tracker"
Write-Host ""
Write-Host "The config file is CRITICAL for performance!" -ForegroundColor Yellow
Write-Host "It excludes node_modules, bin, obj, etc."
Write-Host "Without it, scans will take much longer!"
Write-Host ""
