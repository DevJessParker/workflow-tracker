# Scanner Page Fixed - Local/Cloud Toggle Now Working

## What Was Wrong

The **422 Unprocessable Entity** error was caused by a **data format mismatch** between frontend and backend:

### Frontend was sending:
```json
{
  "repo_path": "/repos/your_repo",
  "source_type": "local",
  "file_extensions": [".cs", ".ts", ".html", ".xaml"],
  "detect_database": true,
  "detect_api": true,
  "detect_files": true,
  "detect_messages": true,
  "detect_transforms": true
}
```

### Backend was expecting:
```json
{
  "repository_path": "/repos/your_repo",  // ❌ Wrong field name!
  "file_types": [".cs", ".ts"],           // ❌ Wrong field name!
  "exclude_patterns": []
}
```

## What Was Fixed

### 1. Updated Backend API Model (`backend/app/api/scanner.py`)

Changed `ScanRequest` to match frontend format:

```python
class ScanRequest(BaseModel):
    """Scan request model - matches frontend format"""
    repo_path: str                          # ✅ Matches frontend
    source_type: str = "local"
    file_extensions: List[str] = [...]      # ✅ Matches frontend
    detect_database: bool = True
    detect_api: bool = True
    detect_files: bool = True
    detect_messages: bool = True
    detect_transforms: bool = True
```

### 2. Enabled Local/Cloud Toggle

Updated `/api/v1/scanner/environment` endpoint to return:

```python
{
    "status": "ready",
    "scanner_version": "1.0.0",
    "supported_languages": ["C#", "TypeScript", "HTML", "XAML"],
    "is_docker": True,
    "supports_local_repos": True,  # ✅ This enables the toggle!
    "supports_github": False,
    "supports_gitlab": False,
    "supports_bitbucket": False,
}
```

The frontend checks `environment.supports_local_repos` to show the Local/Cloud buttons.

### 3. Added Docker Environment Variable

Updated `docker-compose.yml` to set `IS_DOCKER=true`, which:
- Shows the "DOCKER" badge in the UI
- Helps backend know it's running in Docker

## How to Test

### Step 1: Rebuild Docker Containers

```powershell
# Stop containers
docker-compose down

# Rebuild with new code
docker-compose up --build
```

### Step 2: Navigate to Scanner Page

Open: http://localhost:3000/dashboard/scanner

### Step 3: Verify UI Shows Correctly

You should now see:

✅ **"Repository Source" section with two buttons:**
- 📁 **Local** (purple when selected)
- ☁️ **Cloud** (gray when not selected)

✅ **Repository dropdown** below the buttons (when Local is selected)

✅ **"DOCKER" badge** in top-right corner of navigation

✅ **Page title:** "🔍 Workflow Scanner"

### Step 4: Test Scanning

1. Make sure "Local" is selected (purple button)
2. Select a repository from the dropdown
3. Click "Start Scan"

Expected behavior:
- ✅ No more 422 errors!
- ✅ Scan starts successfully
- ✅ Progress bar updates in real-time
- ✅ WebSocket connects (green dot indicator)
- ✅ Files and nodes count increment live

### Step 5: Check Backend Logs

```powershell
docker-compose logs -f backend | Select-String "scan"
```

You should see:
```
[scan_id] ✅ Scan queued, starting background task...
[scan_id] 📁 Repository: /repos/your_repo_name
[scan_id] 📝 File extensions: ['.cs', '.ts', '.html', '.xaml']
[scan_id] 🔍 Detections: DB=True, API=True, Files=True
[scan_id] 📊 Status set to 'discovering' - frontend can now see this
[scan_id] 🔌 WebSocket connected
[scan_id] 📤 Sent progress update
```

## Why the Local/Cloud Toggle Wasn't Showing

The frontend code has a condition:

```typescript
{environment && environment.supports_local_repos && (
  // Local/Cloud toggle only renders when this is true
  <div className="mb-6">
    <label>Repository Source</label>
    <div className="flex space-x-2">
      <button>📁 Local</button>
      <button>☁️ Cloud</button>
    </div>
  </div>
)}
```

Before the fix, the backend was returning:
```json
{
  "status": "ready",
  "scanner_version": "1.0.0",
  "supported_languages": ["C#", "TypeScript", "HTML", "XAML"]
  // ❌ Missing: supports_local_repos!
}
```

Now it returns:
```json
{
  ...
  "supports_local_repos": true  // ✅ Toggle shows!
}
```

## Troubleshooting

### If you still don't see Local/Cloud buttons:

1. **Check environment response:**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scanner/environment"
   ```

   Should show: `"supports_local_repos": true`

2. **Check browser console:**
   - Press F12
   - Look for errors
   - Check Network tab for `/api/v1/scanner/environment` response

3. **Hard refresh browser:**
   - Press Ctrl + Shift + R
   - Or clear cache again

### If you still get 422 errors:

1. **Check backend logs** for validation details:
   ```powershell
   docker-compose logs backend | Select-String "❌"
   ```

2. **Check request body** in browser DevTools:
   - F12 → Network tab
   - Find the POST to `/api/v1/scanner/scan`
   - Look at the Request Payload

3. **Verify field names match:**
   - `repo_path` (not `repository_path`)
   - `file_extensions` (not `file_types`)

## Summary of Changes

### Backend (`backend/app/api/scanner.py`)
- ✅ Updated `ScanRequest` model to match frontend format
- ✅ Changed field names: `repository_path` → `repo_path`, `file_types` → `file_extensions`
- ✅ Added detection flags: `detect_database`, `detect_api`, etc.
- ✅ Added `supports_local_repos: True` to environment endpoint
- ✅ Updated logging to show correct field names

### Docker (`docker-compose.yml`)
- ✅ Added `IS_DOCKER=true` environment variable

### Commits
1. `230139d` - Fix 422 error: Update backend API to match frontend data format
2. `e6c0219` - Add IS_DOCKER environment variable to enable Docker badge in UI

## Next Steps

After rebuilding:

1. ✅ Local/Cloud toggle should appear
2. ✅ 422 errors should be gone
3. ✅ Scanning should work smoothly
4. ✅ Progress bar should update in real-time
5. ✅ WebSocket should connect successfully

**If everything works, you're ready to scan your repositories!** 🎉
