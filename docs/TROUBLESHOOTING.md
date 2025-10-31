# Troubleshooting Guide

This guide addresses common issues when using Workflow Tracker.

## Scan Issues

### Scan appears to hang at a specific file number

**Symptoms:**
```
Scanned 9150/25969 files...
Scanned 9160/25969 files...
[seems to hang]
```

**Diagnosis:** The scan is likely NOT hanging. What you're seeing is:
1. The progress counter updates every 10 files
2. After the last progress update, the scan continues without printing
3. Then it completes and shows the summary

**Solution:** This is expected behavior. Wait for the "Scan complete" message. The scan continues even when it's not printing progress updates.

**If actually hanging:** Check the Docker logs for errors. The scan might have encountered a very large file or complex code pattern.

## Rendering Issues

### Error: "No module named 'scipy'"

**Symptoms:**
```
Error rendering html: No module named 'scipy'
```

**Cause:** scipy is required for Plotly's graph layout algorithms.

**Solution:**
```bash
# Update your dependencies
pip install scipy==1.11.4

# Or reinstall all requirements
pip install -r requirements.txt --upgrade

# For Docker, rebuild the image
docker build -t workflow-tracker .
```

### Warning: "pygraphviz not available"

**Symptoms:**
```
Warning: pygraphviz not available. Skipping png rendering.
Install with: pip install pygraphviz
```

**Cause:** pygraphviz requires system-level Graphviz installation and can be tricky on Windows.

**Solution:**

**Linux/Mac:**
```bash
# Install system dependencies first
sudo apt-get install graphviz graphviz-dev  # Ubuntu/Debian
brew install graphviz                        # macOS

# Then install Python package
pip install pygraphviz
```

**Windows:**
```bash
# Download Graphviz from: https://graphviz.org/download/
# Add to PATH, then:
pip install --global-option=build_ext --global-option="-IC:\Program Files\Graphviz\include" --global-option="-LC:\Program Files\Graphviz\lib" pygraphviz
```

**Alternative:** Use Docker, which includes all dependencies:
```bash
docker build -t workflow-tracker .
docker run --rm -v /path/to/repo:/repo:ro -v ./output:/app/output workflow-tracker scan --repo /repo
```

**Note:** PNG/SVG rendering is optional. HTML and JSON outputs work without pygraphviz.

## Confluence Integration Issues

### Error: "Request too large" (5MB limit exceeded)

**Symptoms:**
```
com.atlassian.plugins.rest.common.limitrequest.RequestEntityTooLargeException:
Request too large. Requests for this resource can be at most 5242880 bytes
```

**Cause:** Your repository has many workflow nodes (e.g., 30K+), and the Confluence page content exceeds the 5MB API limit.

**Solution:** This is now fixed in the latest version! Update to the latest code:

```bash
git pull origin claude/scan-data-workflows-011CUeBpfcn7LqhQHwoFjDNf
```

**What changed:**
- Only first 50 nodes per workflow type are shown in the page
- Full data is attached as `workflow_graph.json`
- Page includes a banner explaining the truncation
- Total page size stays well under 5MB

**To rebuild Docker with the fix:**
```bash
docker build -t workflow-tracker .
```

### Error: "Space not found"

**Symptoms:**
```
Can't find page on the https://yourcompany.atlassian.net/wiki!
```

**Causes:**
1. Incorrect space key
2. Insufficient permissions
3. Personal space key format

**Solutions:**

**Check your space key format:**
- Personal spaces start with `~` (e.g., `~123456789abcdef`)
- Team spaces use uppercase abbreviations (e.g., `DEV`, `DOCS`)

**Find your personal space key:**
1. Go to Confluence → Spaces → Personal
2. Click your personal space
3. Look at the URL: `/wiki/spaces/~123456789abcdef/overview`
4. The part after `/spaces/` is your key

**Verify permissions:**
- You must have permission to create/edit pages in the space
- For team spaces, check with your Confluence admin

**Test with API:**
```bash
curl -u your.email@company.com:YOUR_API_TOKEN \
  https://your-domain.atlassian.net/wiki/rest/api/space/~YOURUSERID
```

### Error: "Authentication failed"

**Causes:**
1. Incorrect API token
2. Wrong email address
3. Expired token

**Solutions:**

**Create a new API token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it "Workflow Tracker"
4. Copy the token immediately (you won't see it again!)
5. Update your `config/local.yaml`:

```yaml
confluence:
  url: "https://your-domain.atlassian.net"
  username: "your.email@company.com"  # Must be the email you log in with
  api_token: "YOUR_NEW_TOKEN_HERE"
  space_key: "~YOUR_USER_ID"
```

**Or use environment variables:**
```bash
export CONFLUENCE_URL="https://your-domain.atlassian.net"
export CONFLUENCE_USERNAME="your.email@company.com"
export CONFLUENCE_API_TOKEN="your-token"
export CONFLUENCE_SPACE_KEY="~YOUR_USER_ID"
```

## Performance Issues

### Scan takes a very long time

**For large repositories (25K+ files):**

This is expected. Scanning time depends on:
- Number of files
- File size
- Complexity of code
- Regex pattern matching

**Benchmarks:**
- ~10K files: 2-5 minutes
- ~25K files: 5-10 minutes
- ~50K+ files: 10-20+ minutes

**Optimization tips:**

1. **Exclude unnecessary directories:**
```yaml
scanner:
  exclude_dirs:
    - "node_modules"
    - "bin"
    - "obj"
    - ".git"
    - "dist"
    - "build"
    - "packages"      # Add this
    - "vendor"        # Add this
    - "test"          # Add this if not scanning tests
```

2. **Limit file extensions:**
```yaml
scanner:
  include_extensions:
    - ".cs"
    - ".ts"
    # Remove .js if you only need .ts files
```

3. **Run in Docker with more memory:**
```bash
docker run --rm -m 4g \
  -v /path/to/repo:/repo:ro \
  -v ./output:/app/output \
  workflow-tracker scan --repo /repo
```

### HTML visualization is very slow to load

**Cause:** With 30K+ nodes, the interactive graph can be slow in the browser.

**Solutions:**

1. **Use the JSON export instead:**
```bash
workflow-tracker scan --repo . --format json
```

2. **Filter by type in the JSON:**
```python
import json
with open('output/workflow_graph.json') as f:
    data = json.load(f)

# Filter to only API calls
api_nodes = [n for n in data['nodes'] if n['type'] == 'api_call']
```

3. **Use the Markdown export for documentation:**
```bash
workflow-tracker scan --repo . --format markdown
```

## Docker Issues

### Container exits immediately

**Check logs:**
```bash
docker logs workflow-tracker
```

**Common issues:**
1. Missing configuration
2. Invalid repository path
3. Permission issues

**Solution - Check your docker-compose.yml:**
```yaml
environment:
  - CONFLUENCE_URL=https://your-domain.atlassian.net
  - CONFLUENCE_USERNAME=your.email@company.com
  - CONFLUENCE_API_TOKEN=your-token
  - CONFLUENCE_SPACE_KEY=~YOUR_USER_ID
```

### Volume mount issues on Windows

**Symptoms:**
```
Error: Repository path not found: /repo
```

**Solution:** Use Windows paths in docker-compose.yml:
```yaml
volumes:
  - C:/Users/yourname/repo:/repo:ro
  - ./output:/app/output
```

Or set environment variable:
```powershell
$env:REPO_TO_SCAN="C:/Users/yourname/repo"
docker-compose up
```

## Development Issues

### ModuleNotFoundError when running locally

**Cause:** Package not installed in development mode.

**Solution:**
```bash
pip install -e .
```

### Tests failing

**Run with verbose output:**
```bash
pytest -v tests/
```

**Common issues:**
1. Missing test dependencies
2. Temporary file cleanup issues

**Solution:**
```bash
pip install -r requirements.txt
pytest --tb=short tests/
```

## Getting Help

If you're still experiencing issues:

1. **Check the full logs:**
```bash
# For Docker
docker logs workflow-tracker > debug.log

# For local runs
workflow-tracker scan --repo . 2>&1 | tee debug.log
```

2. **Enable debug mode:**
```python
# Add to your config
logging:
  level: DEBUG
```

3. **File an issue** with:
   - Full error message
   - Output of `workflow-tracker --version`
   - Repository size (number of files)
   - Operating system
   - Docker version (if using Docker)

4. **Check existing issues:**
   - Search GitHub issues for similar problems
   - Check the CHANGELOG for known issues

## Quick Reference

### Rebuild Docker after updates
```bash
git pull
docker build -t workflow-tracker .
docker-compose down
docker-compose up
```

### Update Python dependencies
```bash
git pull
pip install -r requirements.txt --upgrade
pip install -e .
```

### Clear output directory
```bash
rm -rf output/*
```

### Test configuration
```bash
workflow-tracker scan --repo ./examples --format json
```

This should complete successfully if everything is configured correctly.
