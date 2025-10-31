# Using the Web GUI with Docker

The Workflow Tracker includes a web-based GUI that works perfectly with Docker!

## Quick Start

```powershell
# Start the GUI service
docker-compose up workflow-tracker-gui

# Open your browser to:
http://localhost:8501
```

That's it! The GUI will be available in your browser.

## What You Can Do in the GUI

### 1. **Scan Your Repository Interactively**
- Configure scan options in the sidebar
- Choose which workflow types to detect
- Specify file extensions
- Click "🔍 Scan Repository" to start

### 2. **Generate Diagrams On-Demand**
Once the scan completes:
- Scroll to "📊 Generate Diagrams" section in sidebar
- Choose filter type (Module, Table, or Endpoint)
- Enter filter value (e.g., "Services/UserService")
- Adjust max nodes slider (10-100)
- Click "🎨 Generate Diagram"

### 3. **View and Download Results**
- See scan statistics and charts
- View sample workflow nodes
- Download JSON data
- Download Mermaid diagram code
- Copy diagrams to paste into Confluence

## GUI vs CLI

| Feature | GUI | CLI |
|---------|-----|-----|
| **Interactive** | ✅ Yes | ❌ No |
| **Diagram Generation** | ✅ On-demand button | ✅ Manual script |
| **Confluence Publishing** | ❌ No (local only) | ✅ Yes (with --publish) |
| **Best For** | Local development, testing | CI/CD, automation |

## Important: GUI is Local Only

**The GUI does NOT publish to Confluence.**

This is intentional! The GUI is for:
- Local development and testing
- Generating diagrams to compare before/after changes
- Exploring workflow data interactively

Use the CLI for publishing:
```bash
# After testing in GUI, publish via CLI
docker-compose up workflow-tracker  # with --publish flag in docker-compose.yml
```

## Configuration

The GUI uses the same `config/local.yaml` as the CLI, so your exclusions and settings are respected.

## Accessing from Another Computer

By default, the GUI is only accessible from `localhost` (the computer running Docker).

To access from another computer on your network:

1. **Edit docker-compose.yml:**
```yaml
workflow-tracker-gui:
  ports:
    - "0.0.0.0:8501:8501"  # Allow external access
```

2. **Find your IP address:**
```powershell
# Windows
ipconfig
# Look for "IPv4 Address"
```

3. **Access from other computer:**
```
http://192.168.1.xxx:8501
```

**Security Note:** Only do this on trusted networks!

## Stopping the GUI

```powershell
# Press Ctrl+C in terminal, or:
docker-compose down
```

## Troubleshooting

### GUI Won't Start

**Check if port 8501 is already in use:**
```powershell
# Windows
netstat -ano | findstr :8501

# Linux/Mac
lsof -i :8501
```

**Change the port if needed:**
Edit `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Use port 8502 instead
```

Then access at `http://localhost:8502`

### GUI Shows "Connection Error"

**Wait a few seconds** - Streamlit takes 5-10 seconds to start.

**Check Docker logs:**
```powershell
docker logs workflow-tracker-gui
```

### Can't See My Repository Files

**Check the volume mount** in `docker-compose.yml`:
```yaml
volumes:
  - ${REPO_TO_SCAN:-./}:/repo:ro  # ← Must point to your repo
```

Make sure `REPO_TO_SCAN` in `.env` points to your repository.

## Example Workflow

### 1. **Test Locally with GUI**
```powershell
# Start GUI
docker-compose up workflow-tracker-gui

# Open http://localhost:8501
# Scan repository
# Generate diagrams
# Download and review
```

### 2. **Compare Changes**
```powershell
# Make code changes
# Re-scan in GUI
# Generate diagrams again
# Compare with previous diagrams
```

### 3. **Publish to Confluence**
```powershell
# When ready, publish via CLI
docker-compose down
docker-compose up workflow-tracker  # Publishes to Confluence
```

## Visual Generation

### What Gets Generated Locally

**Always Generated (Fast):**
- ✅ JSON data (complete workflow graph)
- ✅ Markdown documentation
- ✅ Mermaid diagram code (from GUI button)

**Generated for Small/Medium Graphs (<5000 nodes):**
- ✅ Interactive HTML visualization
- ✅ PNG images
- ✅ SVG images

**Skipped for Large Graphs (>5000 nodes):**
- ❌ HTML (would hang - spring layout is O(n²))
- ❌ PNG (would hang)
- ❌ SVG (would hang)

**Why?** With 31,000 nodes, HTML rendering takes hours and may crash.

**Solution:** Use filtered Mermaid diagrams instead (50-100 nodes per diagram).

### Controlling What Gets Published

**Local Generation (Always Happens):**
- Run scan (CLI or GUI)
- Files created in `./output/` directory
- Nothing sent to Confluence

**Confluence Publishing (Only with --publish):**
- Run CLI with `--publish` flag
- Creates parent page "Workflow Documentation"
- Creates child pages with summaries/diagrams
- Attaches JSON/HTML files

**Example:**
```powershell
# Generate locally (no publishing)
docker-compose run --rm workflow-tracker scan --repo /repo

# Generate AND publish
docker-compose up workflow-tracker  # Has --publish in docker-compose.yml
```

## GUI Features

### Real-Time Progress
- See file count as scan progresses
- View node/edge counts
- Track scan time

### Interactive Charts
- Workflow type breakdown
- Bar charts of operations
- Filterable node lists

### Diagram Generation Button
- Filter by module/table/endpoint
- Adjustable node limits
- Download Mermaid code
- Visual preview (if browser supports Mermaid)

### Download Options
- JSON data
- Mermaid diagrams
- HTML visualizations (if generated)

## Summary

**GUI = Local Development Tool**
- Test scans
- Generate diagrams interactively
- Compare workflow changes
- No Confluence publishing

**CLI = Production/CI Tool**
- Automated scans
- Confluence publishing
- CI/CD integration
- Batch processing

Both use the same config and produce the same output formats! 🎉
