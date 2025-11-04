# Scanner Integration Guide

The Workflow Scanner is now integrated into the main Pinata Code web application! No more Streamlit flickering - the scanner runs as a proper web service.

## Architecture

```
Frontend (Next.js)           Backend (FastAPI)          Scanner (Python)
localhost:3000      ←→       localhost:8000      ←→      scanner/
/dashboard/scanner           /api/v1/scanner             graph/builder.py
                                                         graph/renderer.py
```

## Features

### ✅ Dual Repository Support
- **Local Repos** (Docker): Mount your local repositories and scan them
- **Cloud Repos** (Coming Soon): Connect GitHub, GitLab, Bitbucket via OAuth

### ✅ Real-Time Progress
- Live progress bar with file count
- Workflow node detection updates
- Background task processing with FastAPI

### ✅ Rich Visualizations
- **Mermaid Diagrams**: Copy-paste ready workflow diagrams
- **Interactive Results**: Clickable nodes with file locations
- **Summary Statistics**: Files scanned, nodes found, connections

### ✅ Smart Detection
- **Angular**: `(click)="..."`, `this.http.get()`, template/component linking
- **WPF**: `Click="..."`, `HttpClient.GetAsync()`, XAML/code-behind linking
- **Database Operations**: Entity Framework, SaveChanges, queries
- **API Calls**: HTTP methods, endpoints, request/response

## Quick Start (Docker)

### 1. Place Your Repos

Create a `repos` directory and add your repositories:

```bash
mkdir repos
cd repos
git clone https://github.com/your-org/angular-app
git clone https://github.com/your-org/wpf-app
cd ..
```

### 2. Start the Application

```bash
docker-compose up --build
```

This starts:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Access the Scanner

1. Open http://localhost:3000
2. Login (dev mode: any credentials)
3. Navigate to **Scanner** in the top navigation
4. Select your repository from the dropdown
5. Configure file extensions: `.cs,.ts,.html,.xaml`
6. Check detection options (all recommended)
7. Click **Start Scan** 🔍

### 4. View Results

After scanning completes, you'll see:
- **Summary**: Files scanned, nodes found, connections
- **Mermaid Diagram**: Copy to mermaid.live or GitHub
- **Workflow Nodes**: List of all detected UI → API → DB operations

## Configuration

### Environment Variables

**Backend (`.env`):**
```bash
# Local Repository Path (host machine)
LOCAL_REPOS_PATH=./repos

# Or point to existing repos directory
LOCAL_REPOS_PATH=/path/to/your/projects
```

### Docker Compose Override

For custom repository paths, create `docker-compose.override.yml`:

```yaml
services:
  backend:
    volumes:
      - /Users/yourname/Projects:/repos:ro
    environment:
      - LOCAL_REPOS_PATH=/repos
```

## API Endpoints

All scanner endpoints are documented at http://localhost:8000/docs

### Core Endpoints

**Start a Scan:**
```http
POST /api/v1/scanner/scan
Content-Type: application/json

{
  "repo_path": "/repos/your-project",
  "source_type": "local",
  "file_extensions": [".cs", ".ts", ".html", ".xaml"],
  "detect_database": true,
  "detect_api": true,
  "detect_files": true,
  "detect_messages": true,
  "detect_transforms": true
}
```

**Get Scan Status:**
```http
GET /api/v1/scanner/scan/{scan_id}/status
```

**Get Scan Results:**
```http
GET /api/v1/scanner/scan/{scan_id}/results
```

**Get Workflow Diagram:**
```http
GET /api/v1/scanner/scan/{scan_id}/diagram?format=mermaid
```

**List Repositories:**
```http
GET /api/v1/scanner/repositories?source=local
```

**Get Environment Info:**
```http
GET /api/v1/scanner/environment
```

## Frontend Integration

The scanner is integrated at `/dashboard/scanner` in the Next.js frontend.

### Key Components

**Scanner Page** (`frontend/app/dashboard/scanner/page.tsx`):
- Repository selection (dropdown for local, input for cloud)
- Detection options checkboxes
- Real-time progress updates
- Results visualization
- Mermaid diagram display

**State Management:**
```typescript
interface ScanConfig {
  repoPath: string
  sourceType: 'local' | 'github' | 'gitlab' | 'bitbucket'
  fileExtensions: string[]
  detectDatabase: boolean
  detectApi: boolean
  detectFiles: boolean
  detectMessages: boolean
  detectTransforms: boolean
}
```

### Adding to Navigation

The scanner link is already added to the dashboard navigation. To add to other dashboards:

```tsx
<Link href="/dashboard/scanner">
  Scanner
</Link>
```

## Dependencies

### Backend (`backend/pyproject.toml`)

```toml
# Scanner dependencies
networkx = "^3.0"      # Graph construction
plotly = "^5.17.0"     # Visualizations
pandas = "^2.0.0"      # Data analysis
pyyaml = "^6.0"        # Configuration
python-dotenv = "^1.0.0"  # Environment variables
```

### Frontend (`frontend/package.json`)

```json
{
  "dependencies": {
    "mermaid": "^10.6.1",           // Diagram rendering
    "plotly.js": "^2.27.0",         // Interactive charts
    "react-plotly.js": "^2.6.0"    // React wrapper for Plotly
  }
}
```

## Cloud Repository Integration (Coming Soon)

### GitHub Integration

1. Create GitHub OAuth App
2. Add credentials to backend
3. Frontend will show "Connect GitHub" button
4. Users authorize the app
5. Scanner fetches repos via GitHub API
6. Clones temporarily for scanning

### GitLab / Bitbucket

Same OAuth flow with respective provider APIs.

## Troubleshooting

### "No repositories found"

**Problem**: Dropdown is empty in local mode

**Solution**:
1. Check `repos` directory exists: `ls repos/`
2. Check Docker mount: `docker exec pinata-backend ls /repos`
3. Verify permissions: `chmod -R 755 repos/`

### "Repository path not found"

**Problem**: Scan fails with 404 error

**Solution**:
1. Ensure repository path is absolute inside container: `/repos/your-project`
2. Check volume mount in `docker-compose.yml`
3. Restart Docker: `docker-compose restart backend`

### "Scan stuck at 0%"

**Problem**: Progress never updates

**Solution**:
1. Check backend logs: `docker logs pinata-backend`
2. Verify scanner is mounted: `docker exec pinata-backend ls /scanner`
3. Check file extensions match your project

### "WebSocket errors" (Not anymore! 🎉)

**Problem**: The old Streamlit had WebSocket issues

**Solution**: ✅ Fixed! The new FastAPI backend uses HTTP polling instead of WebSockets, eliminating all flickering and connection issues.

## Production Deployment

### Environment Detection

The backend automatically detects the environment:

```python
# Development (Docker): Supports local + cloud repos
ENVIRONMENT=development

# Production: Cloud repos only (for security)
ENVIRONMENT=production
```

### Security Considerations

1. **Local Repos**: Only enable in Docker/dev environments
2. **Cloud Repos**: Use OAuth with minimal scopes (read-only)
3. **Scan Results**: Store in S3 with signed URLs
4. **Rate Limiting**: Implement per-organization scan limits
5. **Resource Limits**: Set max scan duration, file count

## Testing

### Test the Scanner Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/scanner/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/repos/test-project",
    "source_type": "local",
    "file_extensions": [".cs", ".ts"],
    "detect_database": true,
    "detect_api": true
  }'
```

### Check Scan Status

```bash
curl http://localhost:8000/api/v1/scanner/scan/{scan_id}/status
```

### View Results

```bash
curl http://localhost:8000/api/v1/scanner/scan/{scan_id}/results
```

## Development

### Running Frontend Only

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

### Running Backend Only

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

Backend: http://localhost:8000

### Testing Scanner Directly

```bash
cd scanner
python -c "
from scanner.graph.builder import WorkflowGraphBuilder

config = {
    'scanner': {
        'include_extensions': ['.cs', '.ts'],
        'detect': {'database': True, 'api_calls': True}
    }
}

builder = WorkflowGraphBuilder(config)
result = builder.build('/path/to/repo')
print(f'Found {len(result.graph.nodes)} nodes')
"
```

## Next Steps

1. **GitHub OAuth**: Implement cloud repository integration
2. **Real-time Updates**: Add WebSocket support for live progress
3. **Visualization**: Embed interactive Mermaid diagrams
4. **Filtering**: Add advanced filtering by module, file, type
5. **Export**: PDF reports, JSON downloads, CSV exports
6. **Collaboration**: Share scans with team members
7. **History**: View and compare previous scans

## Migration from Streamlit

The old Streamlit app (`scanner/cli/streamlit_app.py`) has been deprecated in favor of the web integration.

### What Changed

- ❌ **Removed**: Streamlit GUI (flickering, WebSocket issues)
- ✅ **Added**: Next.js frontend (stable, no flickering)
- ✅ **Added**: FastAPI backend (proper API, background tasks)
- ✅ **Added**: Docker integration (easy deployment)
- ✅ **Added**: Cloud/local repo toggle (production-ready)

### Benefits

- ✅ No more flickering!
- ✅ Proper authentication
- ✅ Multi-user support
- ✅ Cloud repository integration ready
- ✅ Professional UI/UX
- ✅ API for automation

---

**Built with 🪅 by the Pinata Code Team**
