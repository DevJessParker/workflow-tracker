# Quick Start Guide

Get up and running with Workflow Tracker in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Docker (optional, for containerized deployment)
- Confluence Cloud account with API access

## Step 1: Install (2 minutes)

### Option A: Using Python

```bash
# Clone the repository
git clone <your-repo-url>
cd workflow-tracker

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Verify installation
workflow-tracker --help
```

### Option B: Using Docker

```bash
# Build the image
docker build -t workflow-tracker .

# Verify installation
docker run --rm workflow-tracker --help
```

## Step 2: Configure (2 minutes)

### Create Configuration File

```bash
workflow-tracker init
```

This creates `config/local.yaml`. Edit it with your settings:

```yaml
repository:
  path: "/path/to/your/repo"  # Point to your code

confluence:
  url: "https://your-domain.atlassian.net"
  username: "your.email@company.com"
  api_token: "YOUR_API_TOKEN"  # Get from https://id.atlassian.com/manage-profile/security/api-tokens
  space_key: "~YOUR_USER_ID"    # Your personal space (starts with ~)

scanner:
  include_extensions:
    - ".cs"
    - ".ts"
    - ".js"

output:
  formats:
    - "html"
    - "json"
```

**Quick tip**: Don't have your Confluence API token yet? See [Confluence Setup Guide](CONFLUENCE_SETUP.md)

### Using Environment Variables (Alternative)

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your.email@company.com
CONFLUENCE_API_TOKEN=your-token
CONFLUENCE_SPACE_KEY=~YOUR_USER_ID
```

## Step 3: Run Your First Scan (1 minute)

### Scan and Generate HTML

```bash
workflow-tracker scan --repo /path/to/your/repo --format html
```

Output will be in `./output/workflow_graph.html`

### Scan and Publish to Confluence

```bash
workflow-tracker scan --repo /path/to/your/repo --publish
```

### Use the GUI

```bash
workflow-tracker gui --repo /path/to/your/repo
```

Then open http://localhost:8501 in your browser.

## Step 4: View Results

### Local Files

Check the `output/` directory:
- `workflow_graph.html` - Interactive visualization
- `workflow_graph.json` - Raw data
- `workflow_documentation.md` - Documentation

### Confluence

If you used `--publish`, check your Confluence personal space for a new page titled "Workflow Documentation - {repo-name}"

## What Gets Detected

The tool automatically finds:

✅ **Database Operations**
- Entity Framework queries
- SQL commands
- Database writes (Add, Update, Delete, SaveChanges)

✅ **API Calls**
- HttpClient (C#)
- Angular HttpClient
- Fetch/Axios

✅ **File Operations**
- File.ReadAllText/WriteAllText
- FileReader API

✅ **Message Queues**
- Azure Service Bus
- RabbitMQ

✅ **Data Transformations**
- RxJS operators
- LINQ operations

## Example Output

Running on a typical Angular + C# project:

```
Workflow Tracker
Scanning repository: /path/to/my-app

Found 156 files to scan
Scanned 156/156 files...

Scan complete:
  Files scanned: 156
  Nodes found: 342
  Edges found: 198
  Scan time: 4.23s

Rendering outputs...

✓ Scan complete!

Generated files:
  • HTML: ./output/workflow_graph.html
  • JSON: ./output/workflow_graph.json
```

## Next Steps

### Customize Detection

Edit `config/local.yaml` to control what gets detected:

```yaml
scanner:
  detect:
    database: true
    api_calls: true
    file_io: true
    message_queues: true
    data_transforms: true
```

### Integrate with CI/CD

For TeamCity:
```bash
bash ci-cd/teamcity-build.sh
```

For Octopus Deploy:
```powershell
. ./ci-cd/octopus-deploy.ps1
```

See [README.md](../README.md) for detailed CI/CD setup.

### Try the Examples

We've included sample code to test with:

```bash
workflow-tracker scan --repo ./examples --format html
```

Open `output/workflow_graph.html` to see what the tool detected!

## Troubleshooting

### "No configuration file found"

Run `workflow-tracker init` first.

### "Repository path not found"

Check the `repository.path` in your `config/local.yaml` or pass `--repo` on the command line.

### "No workflows found"

- Make sure your repository has `.cs` or `.ts` files
- Check that `exclude_dirs` isn't filtering out your code
- Verify file extensions in config match your files

### API Token Issues

- Get your token from: https://id.atlassian.com/manage-profile/security/api-tokens
- Make sure to use your email address as the username
- For personal space, space key starts with `~`

## Getting Help

- Check the [full README](../README.md)
- See [Confluence Setup Guide](CONFLUENCE_SETUP.md)
- Review the [example code](../examples/)
- Open an issue on GitHub

## Quick Reference

```bash
# Scan local repository
workflow-tracker scan --repo /path/to/repo

# Scan and publish to Confluence
workflow-tracker scan --repo /path/to/repo --publish

# Launch GUI
workflow-tracker gui

# Specific output formats
workflow-tracker scan --repo . --format html --format json --format png

# Custom config file
workflow-tracker scan --config /path/to/config.yaml

# Custom output directory
workflow-tracker scan --repo . --output ./my-docs
```

## What's Next?

1. ✅ Successfully ran your first scan
2. 📊 Reviewed the HTML visualization
3. 📝 Published to Confluence (optional)
4. 🔧 Customize the configuration for your needs
5. 🚀 Set up CI/CD automation

Happy workflow tracking! 🎉
