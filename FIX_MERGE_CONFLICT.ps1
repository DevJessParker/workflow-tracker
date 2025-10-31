# PowerShell script to fix merge conflict in workflow-tracker

Write-Host "=== Fixing Merge Conflict ===" -ForegroundColor Cyan
Write-Host ""

$conflictFile = "src\integrations\confluence.py"

# Check if file has merge conflict markers
$hasConflict = Select-String -Path $conflictFile -Pattern "<<<<<<< HEAD" -Quiet

if ($hasConflict) {
    Write-Host "Found merge conflict in $conflictFile" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Resolving by accepting all remote changes..." -ForegroundColor Yellow

    # Abort any ongoing merge
    git merge --abort 2>$null

    # Reset to clean state and pull
    git fetch origin claude/scan-data-workflows-011CUeBpfcn7LqhQHwoFjDNf
    git reset --hard origin/claude/scan-data-workflows-011CUeBpfcn7LqhQHwoFjDNf

    Write-Host ""
    Write-Host "SUCCESS: Merge conflict resolved!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Rebuild Docker: docker build --no-cache -t workflow-tracker ." -ForegroundColor White
    Write-Host "2. Run scan: docker-compose up workflow-tracker" -ForegroundColor White
} else {
    Write-Host "No merge conflict found in $conflictFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "If you still see errors, try:" -ForegroundColor Cyan
    Write-Host "  git status" -ForegroundColor White
}
