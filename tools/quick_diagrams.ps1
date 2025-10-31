# Quick Diagrams - PowerShell Helper Script
# This script helps you quickly create common workflow diagrams

param(
    [Parameter(Mandatory=$false)]
    [string]$JsonFile = "output/workflow_graph.json",

    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "diagrams"
)

Write-Host "=== Workflow Diagram Generator ===" -ForegroundColor Cyan
Write-Host ""

# Check if JSON file exists
if (-not (Test-Path $JsonFile)) {
    Write-Host "ERROR: Workflow data not found at $JsonFile" -ForegroundColor Red
    Write-Host "Please run a scan first: docker-compose up workflow-tracker" -ForegroundColor Yellow
    exit 1
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created output directory: $OutputDir" -ForegroundColor Green
}

Write-Host "Loading workflow data..." -ForegroundColor Yellow
$data = Get-Content $JsonFile | ConvertFrom-Json

Write-Host "Found $($data.nodes.Count) workflow nodes" -ForegroundColor Green
Write-Host ""

# Function to create diagram
function Create-Diagram {
    param($Module, $Name)

    Write-Host "Creating diagram for: $Name" -ForegroundColor Cyan
    python tools/create_diagrams.py $JsonFile `
        --module $Module `
        --format mermaid `
        --output "$OutputDir/$Name"

    Write-Host ""
}

# Interactive menu
Write-Host "Select diagram type:" -ForegroundColor Cyan
Write-Host "1. All main services"
Write-Host "2. All controllers"
Write-Host "3. Database operations by table"
Write-Host "4. All API endpoints"
Write-Host "5. Custom module"
Write-Host "6. List available modules"
Write-Host ""

$choice = Read-Host "Enter choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`nSearching for Services..." -ForegroundColor Yellow

        $serviceFiles = $data.nodes |
            Where-Object { $_.location.file -like "*Service*" } |
            Select-Object -ExpandProperty location |
            Select-Object -ExpandProperty file -Unique

        $services = $serviceFiles | ForEach-Object {
            if ($_ -match "Services[/\\](\w+Service)") {
                $matches[1]
            }
        } | Select-Object -Unique

        Write-Host "Found $($services.Count) services`n" -ForegroundColor Green

        foreach ($service in $services | Select-Object -First 10) {
            Create-Diagram "Services/$service" "service_$($service.ToLower())"
        }
    }

    "2" {
        Write-Host "`nSearching for Controllers..." -ForegroundColor Yellow

        $controllerFiles = $data.nodes |
            Where-Object { $_.location.file -like "*Controller*" } |
            Select-Object -ExpandProperty location |
            Select-Object -ExpandProperty file -Unique

        $controllers = $controllerFiles | ForEach-Object {
            if ($_ -match "Controllers[/\\](\w+Controller)") {
                $matches[1]
            }
        } | Select-Object -Unique

        Write-Host "Found $($controllers.Count) controllers`n" -ForegroundColor Green

        foreach ($controller in $controllers | Select-Object -First 10) {
            Create-Diagram "Controllers/$controller" "controller_$($controller.ToLower())"
        }
    }

    "3" {
        Write-Host "`nSearching for database tables..." -ForegroundColor Yellow

        $tables = $data.nodes |
            Where-Object { $_.table_name } |
            Select-Object -ExpandProperty table_name -Unique |
            Sort-Object

        Write-Host "Found tables:" -ForegroundColor Green
        $tables | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }

        Write-Host "`nGenerating diagrams for top tables..." -ForegroundColor Yellow

        foreach ($table in $tables | Select-Object -First 5) {
            Write-Host "Creating diagram for table: $table" -ForegroundColor Cyan
            python tools/create_diagrams.py $JsonFile `
                --table $table `
                --format mermaid `
                --output "$OutputDir/table_$($table.ToLower())"
            Write-Host ""
        }
    }

    "4" {
        Write-Host "`nSearching for API endpoints..." -ForegroundColor Yellow

        $endpoints = $data.nodes |
            Where-Object { $_.endpoint } |
            Select-Object -ExpandProperty endpoint -Unique |
            Sort-Object

        Write-Host "Found endpoints:" -ForegroundColor Green
        $endpoints | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }

        Write-Host "`nGenerating diagrams for endpoints..." -ForegroundColor Yellow

        foreach ($endpoint in $endpoints | Select-Object -First 5) {
            $safeName = $endpoint -replace '[/:]', '_'
            Write-Host "Creating diagram for endpoint: $endpoint" -ForegroundColor Cyan
            python tools/create_diagrams.py $JsonFile `
                --endpoint $endpoint `
                --format mermaid `
                --output "$OutputDir/api$safeName"
            Write-Host ""
        }
    }

    "5" {
        Write-Host "`nEnter module path (e.g., Services/UserService):" -ForegroundColor Yellow
        $module = Read-Host "Module"

        $name = $module -replace '[/\\]', '_'
        Create-Diagram $module "custom_$name"
    }

    "6" {
        Write-Host "`nAnalyzing codebase structure..." -ForegroundColor Yellow
        Write-Host ""

        # Group by directory
        $directories = $data.nodes |
            ForEach-Object { Split-Path $_.location.file } |
            ForEach-Object {
                if ($_ -match '([^/\\]+)[/\\]([^/\\]+)') {
                    "$($matches[1])/$($matches[2])"
                }
            } |
            Group-Object |
            Sort-Object Count -Descending |
            Select-Object -First 20

        Write-Host "Top modules by workflow count:" -ForegroundColor Cyan
        $directories | ForEach-Object {
            Write-Host ("  {0,-40} {1,5} operations" -f $_.Name, $_.Count) -ForegroundColor White
        }

        Write-Host "`nYou can create diagrams for these modules using option 5" -ForegroundColor Yellow
    }

    default {
        Write-Host "Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "✓ Diagram generation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Generated files in: $OutputDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view your diagrams:" -ForegroundColor Yellow
Write-Host "  1. Open a .mmd file in a text editor" -ForegroundColor White
Write-Host "  2. Copy the content" -ForegroundColor White
Write-Host "  3. Paste into https://mermaid.live/" -ForegroundColor White
Write-Host "  4. Export as PNG/SVG" -ForegroundColor White
Write-Host ""

# Open diagrams folder
if (Test-Path $OutputDir) {
    Write-Host "Opening diagrams folder..." -ForegroundColor Green
    Start-Process $OutputDir
}
