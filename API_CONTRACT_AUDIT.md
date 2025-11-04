# API Data Contract Audit Report

**Generated:** 2025-11-04
**Purpose:** Identify mismatches between backend API responses and frontend expected formats

---

## Summary

**Total Endpoints Audited:** 8
**Critical Mismatches Found:** 3
**Minor Issues:** 0
**Passing Contracts:** 5

---

## Critical Mismatches ⚠️

### 1. Node Field: `method` vs `http_method`
- **Severity:** HIGH
- **Impact:** API endpoint HTTP methods not displayed correctly in UI
- **Affected Endpoint:** `GET /api/v1/scanner/scan/{scan_id}/results`

### 2. Edge Field: Missing `edge_type`
- **Severity:** MEDIUM
- **Impact:** Edge type information not available to frontend
- **Affected Endpoint:** `GET /api/v1/scanner/scan/{scan_id}/results`

### 3. Scan Duration Field: `scan_time_seconds` vs `scan_duration`
- **Severity:** LOW
- **Impact:** Scan duration not displayed in results (shows 0s)
- **Affected Endpoint:** `GET /api/v1/scanner/scan/{scan_id}/results`

---

## Detailed Endpoint Analysis

### 1. GET /api/v1/scanner/environment

**Status:** ✅ PASSING

**Backend Response:**
```json
{
  "status": "ready",
  "scanner_version": "1.0.0",
  "supported_languages": ["C#", "TypeScript", "HTML", "XAML"],
  "is_docker": true,
  "supports_local_repos": true,
  "supports_github": false,
  "supports_gitlab": false,
  "supports_bitbucket": false
}
```

**Frontend Expected:**
```typescript
{
  status: string
  scanner_version: string
  supported_languages: string[]
  is_docker: boolean
  supports_local_repos: boolean
  supports_github: boolean
  supports_gitlab: boolean
  supports_bitbucket: boolean
}
```

**Frontend Usage:**
- Line 139: `data.supports_local_repos` ✅
- Line 338: `environment.is_docker` ✅

**Verdict:** Perfect match - no changes needed.

---

### 2. GET /api/v1/scanner/repositories

**Status:** ✅ PASSING

**Backend Response:**
```json
[
  {
    "name": "my-repo",
    "path": "/repos/my-repo",
    "source": "local"
  }
]
```

**Frontend Expected:**
```typescript
Array<{
  name: string
  path: string
  source: string
}>
```

**Frontend Usage:**
- Line 154: `Array.isArray(data)` - Correctly handles array
- Line 419: `repo.name` ✅
- Line 420: `repo.path` ✅

**Verdict:** Perfect match - backend returns array directly as expected.

---

### 3. POST /api/v1/scanner/scan

**Status:** ✅ PASSING

**Backend Request Model:**
```python
{
  "repo_path": str,
  "source_type": str = "local",
  "file_extensions": List[str] = [".cs", ".ts", ".html", ".xaml"],
  "detect_database": bool = True,
  "detect_api": bool = True,
  "detect_files": bool = True,
  "detect_messages": bool = True,
  "detect_transforms": bool = True
}
```

**Backend Response:**
```json
{
  "scan_id": "uuid",
  "status": "queued",
  "message": "Scan started successfully"
}
```

**Frontend Request:**
```typescript
{
  repo_path: string
  source_type: string
  file_extensions: string[]
  detect_database: boolean
  detect_api: boolean
  detect_files: boolean
  detect_messages: boolean
  detect_transforms: boolean
}
```

**Frontend Expected Response:**
```typescript
{
  scan_id: string
  status: string
  message: string
}
```

**Frontend Usage:**
- Line 212: `data.scan_id` ✅
- Line 215: `setScanId(data.scan_id)` ✅

**Verdict:** Perfect match - request and response align completely.

---

### 4. WebSocket /api/v1/scanner/ws/scan/{scan_id}

**Status:** ✅ PASSING

**Backend Messages:**

Connection Message:
```json
{
  "type": "connected",
  "scan_id": "uuid",
  "message": "Connected to scan progress stream"
}
```

Scan Update Message:
```json
{
  "type": "scan_update",
  "scan_id": "uuid",
  "status": "scanning",
  "progress": 45.5,
  "message": "Scanning file 100 of 200",
  "files_scanned": 100,
  "total_files": 200,
  "nodes_found": 150,
  "eta": "2m 30s",
  "timestamp": "now"
}
```

**Frontend Expected:**
```typescript
interface ScanUpdate {
  type: 'connected' | 'scan_update' | 'pong' | 'error'
  scan_id: string
  status?: string
  progress?: number
  message?: string
  files_scanned?: number
  total_files?: number
  nodes_found?: number
  eta?: string
  timestamp: string
}
```

**Frontend Usage:**
- Line 257: `update.scan_id` ✅
- Line 258: `update.status` ✅
- Line 259: `update.progress` ✅
- Line 260: `update.message` ✅
- Line 261: `update.files_scanned` ✅
- Line 262: `update.nodes_found` ✅
- Line 263: `update.eta` ✅
- Line 264: `update.total_files` ✅

**Verdict:** Perfect match - all WebSocket message fields align.

---

### 5. GET /api/v1/scanner/scan/{scan_id}/results

**Status:** ❌ FAILING (3 mismatches)

**Backend Response:**
```json
{
  "scan_id": "uuid",
  "repository_path": "/path/to/repo",
  "files_scanned": 150,
  "nodes": [
    {
      "id": "node-1",
      "type": "database_read",
      "name": "GetUsers",
      "description": "Query users table",
      "location": {
        "file_path": "/path/to/file.cs",
        "line_number": 42
      },
      "metadata": {},
      "table_name": "Users",
      "endpoint": "/api/users",
      "method": "GET"  // ⚠️ MISMATCH: Frontend expects "http_method"
    }
  ],
  "edges": [
    {
      "source": "node-1",
      "target": "node-2",
      "label": "calls",
      "metadata": {}  // ⚠️ MISMATCH: Frontend expects "edge_type"
    }
  ],
  "workflows": [...],
  "scan_time_seconds": 12.5,  // ⚠️ MISMATCH: Frontend expects "scan_duration"
  "errors": []
}
```

**Frontend Expected:**
```typescript
interface ScanResults {
  scan_id: string
  repository_path: string
  files_scanned: number
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  workflows?: UIWorkflow[]
  scan_time_seconds: number
  errors: string[]
}

interface WorkflowNode {
  id: string
  type: string
  name: string
  description: string
  location: {
    file_path: string
    line_number: number
  }
  table_name?: string
  endpoint?: string
  http_method?: string  // ⚠️ EXPECTS http_method
}

interface WorkflowEdge {
  source: string
  target: string
  label: string
  edge_type: string  // ⚠️ EXPECTS edge_type
}
```

**Frontend Usage Issues:**

1. **Line 642:** `scanResults.scan_duration` - Field doesn't exist
   ```typescript
   <div>{(scanResults.scan_duration || 0).toFixed(1)}s</div>
   // Backend sends: scan_time_seconds
   // Frontend expects: scan_duration
   ```

2. **Line 765:** `n.http_method` - Field doesn't exist
   ```typescript
   const methods = [...new Set(endpointNodes.map(n => n.http_method).filter(Boolean))]
   // Backend sends: method
   // Frontend expects: http_method
   ```

3. **Edge type not used:** Frontend expects `edge_type` field but backend only sends `metadata`

**Verdict:** CRITICAL MISMATCHES - requires fixes on backend or frontend.

---

### 6. GET /api/v1/scanner/scan/{scan_id}/diagram

**Status:** ✅ PASSING

**Backend Response:**
```json
{
  "format": "mermaid",
  "diagram": "graph TD\n  A --> B"
}
```

**Frontend Expected:**
```typescript
{
  format: string
  diagram: string
}
```

**Frontend Usage:**
- Line 242: `diagramData.diagram` ✅

**Verdict:** Perfect match - diagram format aligns.

---

### 7. GET /api/v1/scanner/scan/{scan_id}/workflows

**Status:** ✅ NOT USED YET

**Backend Response:**
```json
{
  "scan_id": "uuid",
  "total_workflows": 5,
  "workflows": [...]
}
```

**Frontend Usage:** Not called directly by frontend. Workflows are included in the main results endpoint.

**Verdict:** No issues - endpoint not in use yet.

---

### 8. GET /api/v1/scanner/scan/{scan_id}/workflows/{workflow_id}/diagram

**Status:** ✅ NOT USED YET

**Backend Response:**
```json
{
  "workflow_id": "wf-1",
  "name": "User Login Flow",
  "diagram": "graph TD...",
  "story": "User clicks login button..."
}
```

**Frontend Usage:** Not called by frontend.

**Verdict:** No issues - endpoint not in use yet.

---

## Recommended Fixes

### Option A: Fix Backend (Recommended)

Update `/home/user/workflow-tracker/backend/app/api/scanner.py`:

```python
# Line 228: Change 'method' to 'http_method'
result_json = {
    'scan_id': scan_id,
    'repository_path': result.repository_path,
    'files_scanned': result.files_scanned,
    'nodes': [
        {
            'id': node.id,
            'type': node.type.value,
            'name': node.name,
            'description': node.description,
            'location': {
                'file_path': node.location.file_path,
                'line_number': node.location.line_number,
            },
            'metadata': node.metadata,
            'table_name': node.table_name,
            'endpoint': node.endpoint,
            'http_method': node.method,  # ✅ CHANGE: method -> http_method
        }
        for node in result.graph.nodes
    ],
    'edges': [
        {
            'source': edge.source,
            'target': edge.target,
            'label': edge.label,
            'edge_type': edge.label,  # ✅ ADD: edge_type field
            'metadata': edge.metadata,
        }
        for edge in result.graph.edges
    ],
    'workflows': [...],
    'scan_time_seconds': result.scan_time_seconds,
    'scan_duration': result.scan_time_seconds,  # ✅ ADD: Alias for compatibility
    'errors': result.errors,
}
```

### Option B: Fix Frontend

Update `/home/user/workflow-tracker/frontend/app/dashboard/scanner/page.tsx`:

```typescript
// Line 41: Change http_method to method
interface WorkflowNode {
  id: string
  type: string
  name: string
  description: string
  location: {
    file_path: string
    line_number: number
  }
  table_name?: string
  endpoint?: string
  method?: string  // ✅ CHANGE: http_method -> method
}

// Line 48: Change edge_type to label or remove
interface WorkflowEdge {
  source: string
  target: string
  label: string
  // edge_type: string  // ✅ REMOVE: Not provided by backend
}

// Line 642: Change scan_duration to scan_time_seconds
<div className="text-3xl font-bold text-green-600">
  {(scanResults.scan_time_seconds || 0).toFixed(1)}s
</div>

// Line 765: Change http_method to method
const methods = [...new Set(endpointNodes.map(n => n.method).filter(Boolean))]
```

---

## Impact Analysis

### High Priority Fixes

1. **`http_method` field (Line 765)**
   - **Current Impact:** API endpoint methods not displayed in UI
   - **Affected Feature:** API Endpoints section showing GET/POST/PUT/DELETE badges
   - **User Impact:** Users cannot see which HTTP methods are used for each endpoint

### Medium Priority Fixes

2. **`edge_type` field**
   - **Current Impact:** Edge type information lost
   - **Affected Feature:** Workflow visualization
   - **User Impact:** Less detailed edge metadata available

### Low Priority Fixes

3. **`scan_duration` field (Line 642)**
   - **Current Impact:** Shows 0s for scan duration
   - **Affected Feature:** Metrics dashboard showing scan time
   - **User Impact:** Minor - users don't see actual scan duration

---

## Testing Recommendations

After implementing fixes:

1. **Test scan workflow:**
   ```bash
   # Start a scan
   curl -X POST http://localhost:8000/api/v1/scanner/scan \
     -H "Content-Type: application/json" \
     -d '{"repo_path": "/repos/test", "source_type": "local"}'

   # Get results
   curl http://localhost:8000/api/v1/scanner/scan/{scan_id}/results | jq '.nodes[0]'
   ```

2. **Verify fields:**
   - Check `http_method` appears in node objects
   - Check `edge_type` appears in edge objects
   - Check both `scan_time_seconds` and `scan_duration` present

3. **Test UI:**
   - Navigate to Scanner page
   - Run a scan
   - Verify API endpoints show HTTP method badges (GET, POST, etc.)
   - Verify scan duration displays correctly in metrics

---

## Summary of Changes Needed

### Backend Changes (scanner.py)
- **Line 229:** Change `'method': node.method` to `'http_method': node.method`
- **Line 238:** Add `'edge_type': edge.label` to edge dictionary
- **Line 271:** Add `'scan_duration': result.scan_time_seconds` for backward compatibility

### Frontend Changes (page.tsx)
OR alternatively, update frontend to match backend:
- **Line 41:** Change `http_method?: string` to `method?: string`
- **Line 48:** Remove or change `edge_type: string`
- **Line 642:** Change `scanResults.scan_duration` to `scanResults.scan_time_seconds`
- **Line 765:** Change `n.http_method` to `n.method`

**Recommended Approach:** Fix backend (Option A) to match frontend expectations since frontend field names are more descriptive (`http_method` is clearer than `method`).

---

## File Locations

- **Backend API:** `/home/user/workflow-tracker/backend/app/api/scanner.py`
- **Frontend Page:** `/home/user/workflow-tracker/frontend/app/dashboard/scanner/page.tsx`
- **WebSocket Hook:** `/home/user/workflow-tracker/frontend/app/hooks/useScanWebSocket.ts`

---

## Conclusion

The majority of API contracts are well-aligned between backend and frontend. The three identified mismatches are:

1. ❌ Node field name: `method` → `http_method`
2. ❌ Missing edge field: `edge_type`
3. ❌ Scan duration field: `scan_time_seconds` → `scan_duration`

**Recommendation:** Implement **Option A (Fix Backend)** to align backend responses with frontend expectations. This approach:
- Uses more descriptive field names (`http_method` vs `method`)
- Maintains backward compatibility
- Requires fewer changes across the codebase
- Aligns with REST API best practices (explicit field names)

All other endpoints are working correctly with proper data contract alignment.
