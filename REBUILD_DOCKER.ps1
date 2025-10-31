# PowerShell script to rebuild Docker image with latest fixes

Write-Host "=== Workflow Tracker - Rebuild Script ===" -ForegroundColor Cyan
Write-Host ""

# Stop any running containers
Write-Host "1. Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Pull latest changes (if needed)
Write-Host ""
Write-Host "2. Checking for latest code..." -ForegroundColor Yellow
git pull origin claude/scan-data-workflows-011CUeBpfcn7LqhQHwoFjDNf

# Remove old image to force rebuild
Write-Host ""
Write-Host "3. Removing old Docker image..." -ForegroundColor Yellow
docker rmi workflow-tracker:latest 2>$null
if (-not $?) {
    Write-Host "   No old image to remove" -ForegroundColor Gray
}

# Build new image
Write-Host ""
Write-Host "4. Building new Docker image with latest fixes..." -ForegroundColor Yellow
docker build --no-cache -t workflow-tracker .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Docker image rebuilt successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To verify the fixes are included, run:" -ForegroundColor Cyan
    Write-Host "  docker run --rm workflow-tracker pip list | Select-String scipy" -ForegroundColor White
    Write-Host ""
    Write-Host "You should see: scipy 1.11.4" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To run the scan:" -ForegroundColor Cyan
    Write-Host "  docker-compose up workflow-tracker" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✗ Build failed. Check errors above." -ForegroundColor Red
    exit 1
}
