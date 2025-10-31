# Workflow Tracker

> Automatically scan your codebase and generate interactive workflow documentation

Workflow Tracker is a tool that analyzes C# and TypeScript/Angular repositories to identify and visualize data workflows. It detects database operations, API calls, file I/O, message queues, and data transformations, then generates interactive visualizations and automatically updates your Confluence documentation.

## Features

- **Multi-Language Support**: C# (.NET) and TypeScript/Angular codebases
- **Comprehensive Detection**:
  - Database operations (Entity Framework, ADO.NET, SQL)
  - HTTP/REST API calls
  - File I/O operations
  - Message queues (Azure Service Bus, RabbitMQ)
  - Data transformations (RxJS, LINQ)
  - Cache operations (localStorage, sessionStorage)

- **Multiple Output Formats**:
  - Interactive HTML visualizations
  - Static images (PNG, SVG)
  - JSON data export
  - Markdown documentation
  - Focused Mermaid diagrams (auto-generated or manual)

- **Confluence Integration**: Automatically publish workflow documentation to Confluence Cloud
- **Auto-Generate Diagrams**: Embed focused Mermaid diagrams directly in Confluence (CI/CD mode)
- **Manual Diagram Tools**: Create custom diagrams filtered by module, table, or endpoint
- **CI/CD Ready**: Docker-based deployment for TeamCity and Octopus Deploy
- **Local GUI**: Web-based interface with interactive diagram generation

## Quick Start

### Installation

#### Using Python (Local Development)

```bash
# Clone the repository
git clone <your-repo-url>
cd workflow-tracker

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

#### Using Docker

```bash
# Build the Docker image
docker build -t workflow-tracker .

# Run a scan
docker run --rm \
  -v /path/to/your/repo:/repo:ro \
  -v $(pwd)/output:/app/output \
  workflow-tracker scan --repo /repo
```

### Configuration

1. Create a local configuration file:

```bash
workflow-tracker init
```

2. Edit `config/local.yaml` with your settings:

```yaml
repository:
  path: "/path/to/your/repo"

confluence:
  url: "https://your-domain.atlassian.net"
  username: "your.email@company.com"
  api_token: "your-api-token"
  space_key: "~YOURUSERID"  # Your personal space for testing

scanner:
  include_extensions:
    - ".cs"
    - ".ts"
    - ".js"
  exclude_dirs:
    - "node_modules"
    - "bin"
    - "obj"

output:
  directory: "./output"
  formats:
    - "html"
    - "json"
    - "markdown"
```

3. Get your Confluence API token:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Create a new API token
   - Add it to your configuration

### Usage

#### Command Line

Scan a repository and generate visualizations:

```bash
workflow-tracker scan --repo /path/to/repo --format html --format json
```

Scan and publish to Confluence:

```bash
workflow-tracker scan --repo /path/to/repo --publish
```

Scan and auto-generate diagrams in Confluence (CI/CD):

```bash
workflow-tracker scan --repo /path/to/repo --publish --auto-diagrams
```

Generate focused diagrams manually:

```bash
# After scanning, create diagrams from JSON results
python tools/create_diagrams.py output/workflow_graph.json \
  --module "Services/UserService" \
  --format mermaid \
  --output user_service_diagram
```

#### GUI Mode (Local Development)

Launch the interactive web interface:

```bash
workflow-tracker gui --repo /path/to/repo
```

Then open your browser to http://localhost:8501

Features:
- Scan repository with customizable options
- **Generate diagrams interactively** using the sidebar
- Filter by module, database table, or API endpoint
- Download Mermaid diagrams for documentation
- View and explore workflow nodes in real-time

#### Docker Compose

For easier local development with Docker:

```bash
# Edit .env file with your settings
cp .env.example .env

# Run the scanner
docker-compose up workflow-tracker

# Or run the GUI
docker-compose up workflow-tracker-gui
```

## Diagram Generation

Workflow Tracker provides three ways to generate focused diagrams from your scan results:

### 1. Manual CLI Tool (For Developers)

Generate custom diagrams from scan results for comparing local changes:

```bash
# Generate Mermaid diagram for a specific module
python tools/create_diagrams.py output/workflow_graph.json \
  --module "Services/UserService" \
  --format mermaid \
  --output user_service

# Generate diagram for a database table
python tools/create_diagrams.py output/workflow_graph.json \
  --table Users \
  --format dot \
  --output users_table

# Generate diagram for an API endpoint
python tools/create_diagrams.py output/workflow_graph.json \
  --endpoint "/api/users" \
  --format mermaid
```

**Supported formats:**
- `mermaid` - For Markdown, GitHub, GitLab, Confluence
- `dot` - Graphviz format for high-quality images
- `plantuml` - For sequence diagrams

### 2. Auto-Generate in CI/CD

Configure automatic diagram generation and publishing to Confluence:

```yaml
# In config/local.yaml
confluence:
  auto_diagrams:
    modules:
      - "Services/UserService"
      - "Controllers/UserController"
    tables:
      - "Users"
      - "Orders"
    endpoints:
      - "/api/users"
    max_nodes_per_diagram: 50
```

Then run with `--auto-diagrams` flag:

```bash
workflow-tracker scan --repo . --publish --auto-diagrams
```

Diagrams will be embedded directly in your Confluence page!

### 3. Interactive GUI

Generate diagrams on-demand in the web interface:

1. Launch GUI: `workflow-tracker gui --repo .`
2. Scan your repository
3. Use the "Generate Diagrams" section in the sidebar
4. Select filter type (Module, Table, or Endpoint)
5. Enter filter value and click "Generate Diagram"
6. Download the Mermaid code or copy/paste

**See [docs/AUTO_DIAGRAMS.md](docs/AUTO_DIAGRAMS.md) for complete documentation.**

## CI/CD Integration

### TeamCity

1. Add a build step with the following script:

```bash
#!/bin/bash
# With auto-diagram generation
docker run --rm \
  -v %system.teamcity.build.checkoutDir%:/repo:ro \
  -e CONFLUENCE_URL=%env.CONFLUENCE_URL% \
  -e CONFLUENCE_USERNAME=%env.CONFLUENCE_USERNAME% \
  -e CONFLUENCE_API_TOKEN=%env.CONFLUENCE_API_TOKEN% \
  -e CONFLUENCE_SPACE_KEY=%env.CONFLUENCE_SPACE_KEY% \
  -e CI_MODE=true \
  workflow-tracker:latest \
  scan --repo /repo --publish --auto-diagrams
```

2. Configure environment variables in TeamCity:
   - `CONFLUENCE_URL`
   - `CONFLUENCE_USERNAME`
   - `CONFLUENCE_API_TOKEN`
   - `CONFLUENCE_SPACE_KEY`

3. Update `config/local.yaml` with `auto_diagrams` configuration (see Diagram Generation section)

4. The workflow documentation with embedded diagrams will be automatically updated on each build.

### Octopus Deploy

1. Add a "Run a Script" step to your deployment process

2. Use the PowerShell script:

```powershell
# With auto-diagram generation
docker run --rm `
  -v ${OctopusParameters['Repository.Path']}:/repo:ro `
  -e CONFLUENCE_URL=${OctopusParameters['Confluence.Url']} `
  -e CONFLUENCE_USERNAME=${OctopusParameters['Confluence.Username']} `
  -e CONFLUENCE_API_TOKEN=${OctopusParameters['Confluence.ApiToken']} `
  -e CONFLUENCE_SPACE_KEY=${OctopusParameters['Confluence.SpaceKey']} `
  -e CI_MODE=true `
  workflow-tracker:latest `
  scan --repo /repo --publish --auto-diagrams
```

3. Configure Octopus variables:
   - `Confluence.Url`
   - `Confluence.Username`
   - `Confluence.ApiToken`
   - `Confluence.SpaceKey`
   - `Repository.Path`

4. Update `config/local.yaml` with `auto_diagrams` configuration (see Diagram Generation section)

5. The workflow documentation with embedded diagrams will be updated with each production deployment.

### GitHub Actions (Example)

```yaml
name: Update Workflow Documentation

on:
  push:
    branches: [main]

jobs:
  workflow-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and run Workflow Tracker
        run: |
          docker build -t workflow-tracker .
          docker run --rm \
            -v ${{ github.workspace }}:/repo:ro \
            -v ${{ github.workspace }}/output:/app/output \
            -e CONFLUENCE_URL=${{ secrets.CONFLUENCE_URL }} \
            -e CONFLUENCE_USERNAME=${{ secrets.CONFLUENCE_USERNAME }} \
            -e CONFLUENCE_API_TOKEN=${{ secrets.CONFLUENCE_API_TOKEN }} \
            -e CONFLUENCE_SPACE_KEY=${{ secrets.CONFLUENCE_SPACE_KEY }} \
            -e CI_MODE=true \
            workflow-tracker scan --repo /repo --publish

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: workflow-docs
          path: output/
```

## Architecture

```
workflow-tracker/
├── src/
│   ├── scanner/              # Code scanners
│   │   ├── base.py           # Base scanner class
│   │   ├── csharp_scanner.py # C# code analysis
│   │   └── typescript_scanner.py # TypeScript/Angular analysis
│   ├── graph/                # Graph generation
│   │   ├── builder.py        # Graph construction
│   │   └── renderer.py       # Multi-format rendering
│   ├── integrations/         # External integrations
│   │   └── confluence.py     # Confluence API client
│   ├── cli/                  # Command-line interface
│   │   ├── main.py           # CLI commands
│   │   └── streamlit_app.py  # Web GUI
│   ├── models.py             # Data models
│   └── config_loader.py      # Configuration management
├── config/
│   └── config.example.yaml   # Configuration template
├── ci-cd/                    # CI/CD integration scripts
│   ├── teamcity-build.sh
│   └── octopus-deploy.ps1
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker Compose configuration
└── requirements.txt          # Python dependencies
```

## What Gets Detected

### C# (.NET) Detection

- **Database Operations**:
  - Entity Framework LINQ queries
  - DbContext operations (Add, Update, Remove, SaveChanges)
  - Raw SQL queries (SqlCommand, ExecuteReader, etc.)
  - Dapper queries

- **API Calls**:
  - HttpClient requests (GetAsync, PostAsync, etc.)
  - RestSharp calls
  - Custom HTTP clients

- **File Operations**:
  - File.ReadAllText/WriteAllText
  - StreamReader/StreamWriter
  - FileStream operations

- **Message Queues**:
  - Azure Service Bus (ServiceBusSender, ServiceBusReceiver)
  - RabbitMQ (BasicPublish, BasicConsume)

### TypeScript/Angular Detection

- **API Calls**:
  - Angular HttpClient methods
  - Fetch API
  - Axios requests

- **Storage Operations**:
  - localStorage/sessionStorage
  - IndexedDB

- **Data Transformations**:
  - RxJS operators (map, filter, switchMap, etc.)
  - Array operations

- **File Operations**:
  - FileReader API
  - Blob operations

## Output Examples

### Interactive HTML Visualization

The HTML output provides an interactive graph where you can:
- Zoom and pan
- Hover over nodes to see details
- Click nodes to view code snippets
- Filter by workflow type

### Confluence Documentation

Automatically generated pages include:
- Summary statistics
- Workflow operation breakdown by type
- Detailed listings with code snippets
- Attached interactive visualizations

### JSON Export

Perfect for programmatic access:

```json
{
  "repository": "/path/to/repo",
  "nodes": [
    {
      "id": "UserService.cs:db_read:45",
      "type": "database_read",
      "name": "DB Query: Users",
      "location": {
        "file": "Services/UserService.cs",
        "line": 45
      },
      "table_name": "Users"
    }
  ],
  "edges": [
    {
      "source": "UserService.cs:db_read:45",
      "target": "UserService.cs:transform:52",
      "label": "Data Processing"
    }
  ]
}
```

## Configuration Options

See `config/config.example.yaml` for all available options:

- **Repository settings**: Path, branch
- **Confluence settings**: URL, credentials, space
- **Scanner settings**: File extensions, excluded directories, detection toggles
- **Output settings**: Formats, directory, visualization options
- **CI mode**: Headless execution, error handling

## Troubleshooting

### "No configuration file found"

Run `workflow-tracker init` to create the configuration template.

### "Confluence API error"

- Verify your API token is correct
- Check that your space key is correct (for personal space, it starts with `~`)
- Ensure you have permission to create/edit pages in the space

### "No workflows found"

- Check that file extensions in config match your repository
- Verify excluded directories aren't filtering out your code
- Try running with `--debug` flag for more information

### Docker issues

- Make sure the repository path is mounted correctly
- Check that output directory has write permissions
- Verify environment variables are set

## Development

### Adding a New Scanner

1. Create a new scanner class inheriting from `BaseScanner`:

```python
from src.scanner.base import BaseScanner
from src.models import WorkflowGraph, WorkflowNode, WorkflowType

class MyLanguageScanner(BaseScanner):
    def can_scan(self, file_path: str) -> bool:
        return file_path.endswith('.mylang')

    def scan_file(self, file_path: str) -> WorkflowGraph:
        # Implement scanning logic
        pass
```

2. Register it in `src/graph/builder.py`:

```python
scanners = [
    CSharpScanner(scanner_config),
    TypeScriptScanner(scanner_config),
    MyLanguageScanner(scanner_config),  # Add your scanner
]
```

### Running Tests

```bash
pytest tests/ -v
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact your team lead
- Check the documentation in `docs/`

## Roadmap

Future enhancements:
- [ ] Support for Java/Spring Boot
- [ ] Support for Python/Django
- [ ] GraphQL query detection
- [ ] gRPC call detection
- [ ] Cloud service integrations (AWS, Azure)
- [ ] Performance profiling integration
- [ ] Custom pattern definitions
- [ ] Team collaboration features
