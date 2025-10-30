# Octopus Deploy PowerShell Script for Workflow Tracker
# This script runs as part of your deployment process to update workflow documentation

Write-Host "=== Workflow Tracker - Octopus Deploy Integration ===" -ForegroundColor Cyan

# Get Octopus variables (configure these in your Octopus project)
$confluenceUrl = $OctopusParameters['Confluence.Url']
$confluenceUsername = $OctopusParameters['Confluence.Username']
$confluenceApiToken = $OctopusParameters['Confluence.ApiToken']
$confluenceSpaceKey = $OctopusParameters['Confluence.SpaceKey']
$repoPath = $OctopusParameters['Repository.Path']

# Validate parameters
if (-not $confluenceUrl -or -not $confluenceUsername -or -not $confluenceApiToken -or -not $confluenceSpaceKey) {
    Write-Error "Missing required Confluence configuration. Please set Octopus variables."
    exit 1
}

# Check if Docker is available
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Using Docker to run Workflow Tracker..." -ForegroundColor Green

    # Build Docker image
    Write-Host "Building Docker image..."
    docker build -t workflow-tracker:latest .

    # Run workflow scan
    Write-Host "Scanning repository and publishing to Confluence..."
    docker run --rm `
        -v "${repoPath}:/repo:ro" `
        -v "${PWD}/output:/app/output" `
        -e CONFLUENCE_URL="$confluenceUrl" `
        -e CONFLUENCE_USERNAME="$confluenceUsername" `
        -e CONFLUENCE_API_TOKEN="$confluenceApiToken" `
        -e CONFLUENCE_SPACE_KEY="$confluenceSpaceKey" `
        -e CI_MODE=true `
        workflow-tracker:latest `
        scan --repo /repo --publish

} else {
    Write-Host "Docker not found. Using Python directly..." -ForegroundColor Yellow

    # Check Python
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python is required but not installed."
        exit 1
    }

    # Install dependencies
    Write-Host "Installing Python dependencies..."
    python -m pip install -r requirements.txt

    # Set environment variables
    $env:CONFLUENCE_URL = $confluenceUrl
    $env:CONFLUENCE_USERNAME = $confluenceUsername
    $env:CONFLUENCE_API_TOKEN = $confluenceApiToken
    $env:CONFLUENCE_SPACE_KEY = $confluenceSpaceKey
    $env:CI_MODE = "true"

    # Run workflow tracker
    Write-Host "Scanning repository and publishing to Confluence..."
    python -m src.cli.main scan --repo $repoPath --publish
}

Write-Host "✓ Workflow documentation updated successfully!" -ForegroundColor Green

# Set Octopus output variable with the output directory
Set-OctopusVariable -name "WorkflowDocs.OutputPath" -value "$PWD/output"
