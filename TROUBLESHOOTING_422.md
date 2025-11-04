# Troubleshooting 422 Error and Scanner UI Issues

## Problem
- Getting 422 Unprocessable Entity when starting a scan
- Scanner page doesn't show repository dropdown (shows text input instead)

## Root Cause
**Browser cache** is serving an old version of the scanner page.

## Solution

### Step 1: Clear Browser Cache and Hard Refresh

**In your browser (on http://localhost:3000/dashboard/scanner):**

#### Chrome/Edge:
1. Press `Ctrl + Shift + Delete` (or `Cmd + Shift + Delete` on Mac)
2. Select "Cached images and files"
3. Click "Clear data"
4. Then press `Ctrl + F5` to hard refresh (or `Cmd + Shift + R` on Mac)

#### Or use DevTools:
1. Press `F12` to open DevTools
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Step 2: Verify the Correct Page is Loading

After clearing cache, you should see:

✅ **Correct Scanner Page Features:**
- Title: "Code Scanner" (not "Workflow Scanner")
- **Repository dropdown** (NOT a text input for path)
- "Start Scan" button
- Real-time progress bar when scanning
- Connection status indicator (green dot when connected)
- WebSocket status logs in console

❌ **Old Cached Page (Wrong):**
- Title: "Workflow Scanner"
- Text input for "Repository Path"
- Text input for "File Extensions"
- No repository dropdown

### Step 3: Check Backend Logs

With the debugging enhancements, if you still get a 422 error, the backend will now log:

```
❌ Validation error on POST /api/v1/scanner/scan
❌ Error details: [... detailed error info ...]
❌ Request body: {...actual JSON sent...}
```

This will tell us exactly what's wrong with the request.

### Step 4: Test the Scanner

Once you see the correct page:

1. **Select a repository** from the dropdown
   - Should auto-populate with repositories from `/repos` directory

2. **Click "Start Scan"**
   - Button should disable and show "Scanning..."
   - Connection indicator should turn green
   - Progress bar should start updating smoothly

3. **Watch the logs**
   ```powershell
   docker-compose logs -f backend | Select-String "scan"
   ```

Expected output:
```
[scan_id] ✅ Scan queued, starting background task...
[scan_id] 📁 Repository: /repos/your_repo
[scan_id] 📝 File types: ['.cs', '.ts', '.html', '.xaml']
[scan_id] 🚫 Exclude patterns: ['node_modules', 'bin', ...]
[scan_id] 📊 Status set to 'discovering' - frontend can now see this
[scan_id] 🔌 WebSocket connected
[scan_id] 📤 Sent progress update
```

## If You Still See "Workflow Scanner" After Clearing Cache

The containers might have cached the old build. Rebuild everything:

```powershell
# Stop containers
docker-compose down

# Remove frontend image to force rebuild
docker rmi workflow-tracker-frontend

# Rebuild and start
docker-compose up --build
```

## If You Still Get 422 After Fixing Cache

Check the backend logs for the validation error details:

```powershell
docker-compose logs backend | Select-String "❌"
```

The error will show:
1. Which field is invalid
2. What value was received
3. What value was expected

Common issues:
- `file_types` sent as string instead of array
- `repository_path` is empty or null
- Request format doesn't match `ScanRequest` model

## Backend API Expected Format

The `/api/v1/scanner/scan` endpoint expects:

```json
{
  "repository_path": "/repos/your_repo_name",
  "file_types": [".cs", ".ts", ".html", ".xaml"],
  "exclude_patterns": ["node_modules", "bin", "obj", ".git"]
}
```

**Key points:**
- `repository_path`: **string** (required)
- `file_types`: **array of strings** (optional, has defaults)
- `exclude_patterns`: **array of strings** (optional, has defaults)

## Testing the API Directly

You can test the backend directly to verify it works:

```powershell
# Test with curl (in PowerShell)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scanner/scan" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"repository_path":"/repos/igsolutions_repo","file_types":[".cs",".ts",".html",".xaml"]}'
```

Should return:
```json
{
  "scan_id": "uuid-here",
  "status": "queued",
  "message": "Scan started successfully"
}
```

## Next Steps

1. ✅ Clear browser cache completely
2. ✅ Hard refresh the scanner page
3. ✅ Verify you see the repository dropdown
4. ✅ Select a repository and start scan
5. ✅ Watch progress bar update in real-time

If issues persist after all these steps, share:
- Backend logs from the `❌ Validation error` output
- Browser console logs
- Screenshot of the scanner page
