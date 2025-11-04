# API Data Contracts - Standardized Reference

## Overview

This document defines the **standardized data contracts** between the backend API and frontend. All endpoints have been audited and verified to ensure alignment.

**Last Audit:** 2025-11-04
**Status:** ✅ All contracts passing

---

## Endpoint Contracts

### 1. GET /api/v1/scanner/environment

**Purpose:** Get scanner environment information

**Response:**
```typescript
{
  status: "ready" | "error"
  scanner_version: string
  supported_languages: string[]
  is_docker: boolean
  supports_local_repos: boolean
  supports_github: boolean
  supports_gitlab: boolean
  supports_bitbucket: boolean
}
```

**Example:**
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

---

### 2. GET /api/v1/scanner/repositories?source=local

**Purpose:** Get available repositories for scanning

**Query Parameters:**
- `source`: "local" | "github" | "gitlab" | "bitbucket"

**Response:**
```typescript
Array<{
  name: string
  path: string
  source: string
}>
```

**Example:**
```json
[
  {
    "name": "igsolutions_repo",
    "path": "/repos/igsolutions_repo",
    "source": "local"
  }
]
```

---

### 3. POST /api/v1/scanner/scan

**Purpose:** Start a new code scan

**Request Body:**
```typescript
{
  repo_path: string
  source_type: "local" | "github" | "gitlab" | "bitbucket"
  file_extensions: string[]  // e.g., [".cs", ".ts", ".html", ".xaml"]
  detect_database: boolean
  detect_api: boolean
  detect_files: boolean
  detect_messages: boolean
  detect_transforms: boolean
}
```

**Response:**
```typescript
{
  scan_id: string      // UUID
  status: "queued"
  message: string
}
```

**Example Request:**
```json
{
  "repo_path": "/repos/igsolutions_repo",
  "source_type": "local",
  "file_extensions": [".cs", ".ts", ".html", ".xaml"],
  "detect_database": true,
  "detect_api": true,
  "detect_files": true,
  "detect_messages": true,
  "detect_transforms": true
}
```

**Example Response:**
```json
{
  "scan_id": "9408815b-a1f0-42eb-9d1d-c8c1987d6fe8",
  "status": "queued",
  "message": "Scan started successfully"
}
```

---

### 4. WebSocket /api/v1/scanner/ws/scan/{scan_id}

**Purpose:** Real-time scan progress updates

**Message Types:**

#### Connection Confirmation
```typescript
{
  type: "connected"
  scan_id: string
  message: string
}
```

#### Scan Update
```typescript
{
  type: "scan_update"
  scan_id: string
  status: "discovering" | "scanning" | "completed" | "error" | "failed"
  progress: number        // 0-100
  message: string
  files_scanned: number
  total_files?: number
  nodes_found: number
  eta?: string
  timestamp: string
}
```

#### Pong (Heartbeat)
```typescript
{
  type: "pong"
  scan_id: string
  timestamp: string
}
```

#### Error
```typescript
{
  type: "error"
  scan_id: string
  message: string
  timestamp: string
}
```

---

### 5. GET /api/v1/scanner/scan/{scan_id}/results

**Purpose:** Get complete scan results

**Response:**
```typescript
{
  scan_id: string
  repository_path: string
  files_scanned: number
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  workflows: UIWorkflow[]
  scan_time_seconds: number
  scan_duration: number      // Alias for scan_time_seconds
  errors: string[]
}

interface WorkflowNode {
  id: string
  type: string              // "database_read", "database_write", "api_call", etc.
  name: string
  description: string
  location: {
    file_path: string
    line_number: number
  }
  metadata: Record<string, any>
  table_name?: string       // For database operations
  endpoint?: string         // For API calls
  http_method?: string      // For API calls: "GET", "POST", etc.
}

interface WorkflowEdge {
  source: string           // Node ID
  target: string           // Node ID
  label: string
  edge_type: string        // Same as label
  metadata: Record<string, any>
}

interface UIWorkflow {
  id: string
  name: string
  summary: string          // Plain language summary
  outcome: string          // What user sees at end
  trigger: {
    name: string
    description: string
    interaction_type: string  // "button_click", "form_submit", etc.
    component: string
    location: string
  }
  steps: Array<{
    step_number: number
    title: string
    description: string      // Plain language
    technical_details: string
    icon: string            // Emoji
    node_id: string
  }>
  story: string            // Complete markdown narrative
}
```

**Example:**
```json
{
  "scan_id": "9408815b-a1f0-42eb-9d1d-c8c1987d6fe8",
  "repository_path": "/repos/igsolutions_repo",
  "files_scanned": 8893,
  "nodes": [
    {
      "id": "node-1",
      "type": "database_read",
      "name": "GetUsers",
      "description": "Query users from database",
      "location": {
        "file_path": "/repos/app/Controllers/UserController.cs",
        "line_number": 42
      },
      "metadata": {},
      "table_name": "Users",
      "endpoint": null,
      "http_method": null
    },
    {
      "id": "node-2",
      "type": "api_call",
      "name": "UpdateUserProfile",
      "description": "Call external API to update profile",
      "location": {
        "file_path": "/repos/app/Services/UserService.cs",
        "line_number": 156
      },
      "metadata": {},
      "table_name": null,
      "endpoint": "/api/users/profile",
      "http_method": "POST"
    }
  ],
  "edges": [
    {
      "source": "node-1",
      "target": "node-2",
      "label": "Sequential",
      "edge_type": "Sequential",
      "metadata": {"distance": 5}
    }
  ],
  "workflows": [
    {
      "id": "workflow_abc123",
      "name": "Save Customer Button",
      "summary": "This workflow retrieves data from 1 table, saves to 2 tables",
      "outcome": "Data is saved and user sees confirmation",
      "trigger": {
        "name": "Save Customer Button",
        "description": "User clicks Save Customer Button",
        "interaction_type": "button_click",
        "component": "CustomerForm",
        "location": "/repos/app/Views/CustomerForm.tsx"
      },
      "steps": [
        {
          "step_number": 1,
          "title": "Retrieve data from Customers table",
          "description": "The system looks up existing information from the Customers table.",
          "technical_details": "Database SELECT: Customers",
          "icon": "📖",
          "node_id": "node-1"
        }
      ],
      "story": "# Save Customer Information\n\n..."
    }
  ],
  "scan_time_seconds": 125.5,
  "scan_duration": 125.5,
  "errors": []
}
```

---

### 6. GET /api/v1/scanner/scan/{scan_id}/diagram?format=mermaid

**Purpose:** Get technical workflow diagram

**Query Parameters:**
- `format`: "mermaid" | "json"

**Response (format=mermaid):**
```typescript
{
  format: "mermaid"
  diagram: string  // Mermaid syntax
}
```

**Response (format=json):**
```typescript
{
  format: "json"
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}
```

**Example:**
```json
{
  "format": "mermaid",
  "diagram": "graph TD\n    node_1[(\"GetUsers<br/>database_read\")]\n    node_2([\"UpdateUserProfile<br/>api_call\"])\n    node_1 --> node_2"
}
```

---

### 7. GET /api/v1/scanner/scan/{scan_id}/workflows

**Purpose:** Get all UI workflows

**Response:**
```typescript
{
  scan_id: string
  total_workflows: number
  workflows: UIWorkflow[]
}
```

**Example:**
```json
{
  "scan_id": "9408815b-a1f0-42eb-9d1d-c8c1987d6fe8",
  "total_workflows": 5,
  "workflows": [...]
}
```

---

### 8. GET /api/v1/scanner/scan/{scan_id}/workflows/{workflow_id}/diagram

**Purpose:** Get user-friendly diagram for specific workflow

**Response:**
```typescript
{
  workflow_id: string
  name: string
  diagram: string      // Mermaid syntax with colors and styling
  story: string        // Markdown narrative
}
```

**Example:**
```json
{
  "workflow_id": "workflow_abc123",
  "name": "Save Customer Button",
  "diagram": "graph TD\n    classDef userAction fill:#4CAF50...",
  "story": "# Save Customer Information\n\n**What happens:** ..."
}
```

---

## Validation Rules

### Required Fields

All endpoints must return these fields at minimum:
- Successful responses: Include all documented fields
- Error responses: `{ "error": string, "detail"?: any }`

### Type Safety

- All UUIDs must be valid v4 UUIDs
- All numbers must be finite
- All arrays must be valid (can be empty)
- All objects must have all required fields

### Backward Compatibility

When adding new fields:
- ✅ **Safe:** Adding optional fields
- ✅ **Safe:** Adding new endpoints
- ❌ **Breaking:** Removing fields
- ❌ **Breaking:** Changing field types
- ❌ **Breaking:** Renaming fields

---

## Common Data Types

### WorkflowType Values

```typescript
type WorkflowType =
  | "database_read"
  | "database_write"
  | "api_call"
  | "file_read"
  | "file_write"
  | "message_send"
  | "message_receive"
  | "data_transform"
  | "cache_read"
  | "cache_write"
```

### ScanStatus Values

```typescript
type ScanStatus =
  | "queued"        // Scan just started
  | "discovering"   // Finding files
  | "scanning"      // Analyzing code
  | "completed"     // Successfully finished
  | "error"         // Failed with error
  | "failed"        // Failed (alternative)
```

### HTTPMethod Values

```typescript
type HTTPMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "OPTIONS"
  | "HEAD"
```

---

## Testing Checklist

When making changes to API contracts:

- [ ] Update backend response format
- [ ] Update frontend TypeScript interfaces
- [ ] Update this documentation
- [ ] Test all affected endpoints
- [ ] Verify frontend displays data correctly
- [ ] Check browser console for errors
- [ ] Run API contract audit script

---

## Troubleshooting

### "Cannot read properties of undefined"

**Cause:** Frontend trying to access field that doesn't exist in backend response

**Solution:**
1. Check `/docs/API_CONTRACTS.md` for correct field names
2. Verify backend sends all required fields
3. Check TypeScript interface matches response

### Missing data in UI

**Cause:** Field name mismatch between backend and frontend

**Solution:**
1. Run API contract audit: Check `API_CONTRACT_AUDIT.md`
2. Fix mismatched field names
3. Rebuild backend and frontend

### Type errors in TypeScript

**Cause:** Interface doesn't match API response structure

**Solution:**
1. Update TypeScript interface to match this document
2. Ensure all optional fields are marked with `?`
3. Use correct data types

---

## Change Log

### 2025-11-04
- ✅ Standardized all contracts
- ✅ Fixed `method` → `http_method` mismatch
- ✅ Added `edge_type` field to edges
- ✅ Added `scan_duration` alias
- ✅ Verified all 8 endpoints passing

---

## Support

For questions or to report mismatches:
1. Check this documentation first
2. Review `API_CONTRACT_AUDIT.md` for detailed analysis
3. Run audit script to verify all contracts
4. Open issue with "API Contract" label
