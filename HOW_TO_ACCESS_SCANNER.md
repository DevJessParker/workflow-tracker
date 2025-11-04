# 🚀 How to Access the Scanner

## Quick Start (3 Steps)

### 1. Make Sure Docker is Running

```powershell
# In your workflow-tracker directory
cd C:\Users\jparker\github\workflow-tracker

# Start the app
docker-compose up --build
```

Wait for all services to start. You should see:
```
pinata-frontend    |  ✓ Ready in 2.1s
pinata-backend     | ✅ Backend ready!
```

### 2. Open the Web App

Open your browser and go to:
```
http://localhost:3000
```

You'll see the **Pinata Code landing page** with the big 🪅 pinata icon.

### 3. Login (Dev Mode)

Click the **"Log in"** button in the top right.

On the login page, you'll see a yellow **"Development Mode"** banner. Click:
```
Skip Auth (Dev Only)
```

You'll be logged in automatically as a dev user and redirected to the dashboard!

### 4. Access the Scanner

Once on the dashboard, look at the **top navigation bar**. You'll see these links:
- Dashboard
- **Scanner** ← Click this!
- Repositories
- Scans

Click **Scanner** to access the workflow scanner page.

## Scanner Page Features

On the scanner page you can:

1. **Select Repository Source**
   - **Local**: Select from mounted Docker repositories (if you have any in `/repos`)
   - **Cloud**: Enter GitHub/GitLab URLs (coming soon)

2. **Configure Scan**
   - **Repository Path**: Enter path or select from dropdown
   - **File Extensions**: `.cs,.ts,.html,.xaml` (for Angular + WPF)
   - **Detection Options**: Check which operations to detect

3. **Start Scan**
   - Click **🔍 Start Scan**
   - Watch real-time progress bar
   - See file count and node count updates

4. **View Results**
   - See summary statistics (files scanned, nodes found)
   - View Mermaid workflow diagram
   - Explore detected workflow nodes
   - Click on nodes to see file locations

## Testing with Your Angular/WPF Repository

### Option 1: Mount Your Repository

1. **Stop Docker**:
   ```powershell
   docker-compose down
   ```

2. **Create repos directory**:
   ```powershell
   mkdir repos
   ```

3. **Copy your project** (or symlink):
   ```powershell
   # Copy approach
   xcopy /E /I "C:\path\to\your\angular-project" "repos\angular-app"
   xcopy /E /I "C:\path\to\your\wpf-project" "repos\wpf-app"

   # Or use mklink for symbolic link
   mklink /D "repos\angular-app" "C:\path\to\your\angular-project"
   ```

4. **Restart Docker**:
   ```powershell
   docker-compose up --build
   ```

5. **In Scanner**: Select your repository from the dropdown!

### Option 2: Use Direct Path (Linux Path in Docker)

1. Configure `docker-compose.yml` to mount your Windows path:
   ```yaml
   backend:
     volumes:
       - C:\Users\jparker\Projects:/projects:ro
   ```

2. In Scanner, enter:
   ```
   /projects/your-angular-app
   ```

## Troubleshooting

### "Cannot access scanner page"

**Problem**: Page not found or blank

**Solution**:
1. Make sure you're logged in (click "Skip Auth (Dev Only)")
2. Check the URL is exactly: `http://localhost:3000/dashboard/scanner`
3. Check browser console for errors (F12)

### "No repositories in dropdown"

**Problem**: Local dropdown is empty

**Solution**:
1. Make sure you have repositories in `./repos` directory
2. Check Docker mount: `docker exec pinata-backend ls /repos`
3. Try entering path manually instead

### "Backend not responding"

**Problem**: API calls fail

**Solution**:
1. Check backend logs: `docker logs pinata-backend`
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check for import errors in the logs

### "Frontend not loading"

**Problem**: http://localhost:3000 shows nothing

**Solution**:
1. Check frontend logs: `docker logs pinata-frontend`
2. Make sure port 3000 isn't in use by another app
3. Try `docker-compose restart frontend`

## API Endpoints (for testing)

You can also test the scanner via API:

### Start a Scan
```powershell
curl -X POST http://localhost:8000/api/v1/scanner/scan `
  -H "Content-Type: application/json" `
  -d '{
    "repo_path": "/repos/your-project",
    "source_type": "local",
    "file_extensions": [".cs", ".ts", ".html", ".xaml"],
    "detect_database": true,
    "detect_api": true
  }'
```

### Check Scan Status
```powershell
curl http://localhost:8000/api/v1/scanner/scan/{scan_id}/status
```

### Get Results
```powershell
curl http://localhost:8000/api/v1/scanner/scan/{scan_id}/results
```

### View API Docs
Open: http://localhost:8000/docs

## Full User Flow

```
1. http://localhost:3000
   └─> Landing page with 🪅 pinata

2. Click "Log in" button
   └─> Login page with dev bypass

3. Click "Skip Auth (Dev Only)"
   └─> Dashboard page with navigation

4. Click "Scanner" in navigation
   └─> Scanner page at /dashboard/scanner

5. Configure and click "Start Scan"
   └─> See progress bar with 🪅 animation

6. View results
   └─> Mermaid diagrams, node list, statistics
```

## What You Should See

### Landing Page (localhost:3000)
```
🪅 Pinata Code
It's What's Inside That Counts

[Log in] [Start Free] buttons
```

### After Login (localhost:3000/dashboard)
```
🪅 Pinata Code
Dashboard | Scanner | Repositories | Scans
```

### Scanner Page (localhost:3000/dashboard/scanner)
```
🔍 Workflow Scanner

[Configuration Panel]     [Results Panel]
- Repository Source       - Progress bar
- Repository Path         - Summary stats
- File Extensions         - Workflow diagram
- Detection Options       - Node list
[🔍 Start Scan]
```

## Next Steps

- See **[SCANNER_INTEGRATION.md](SCANNER_INTEGRATION.md)** for complete documentation
- Check **[backend API docs](http://localhost:8000/docs)** for endpoint details
- Read **[README.md](README.md)** for project overview

---

**Having issues?** Check the Docker logs:
```powershell
docker-compose logs frontend
docker-compose logs backend
```
