# Quick Reference: Entity Detection Summary

## Entity Types Matrix

### 1. DATABASE ENTITIES - Status: FULLY IMPLEMENTED (Two-Pass)

| Aspect | Status | Details |
|--------|--------|---------|
| **Definitions** | ✅ Detected | DbContext, DbSet<T>, [Table] attributes |
| **Usage** | ✅ Detected | .Where(), .Select(), .SaveChanges() |
| **Registry** | ✅ Implemented | `schemas_discovered` in ScanResult |
| **Cross-File** | ✅ Supported | Entity classes in separate files |
| **Method** | Two-Pass | First: discover, Second: resolve + use |
| **Files** | csharp_scanner.py | detect_schemas(), _detect_dbsets(), _detect_entity_classes() |

---

### 2. API ROUTES - Status: INCOMPLETE (Usage Detected, Definitions Missing)

| Aspect | Status | Details |
|--------|--------|---------|
| **Definitions** | ❌ NOT Detected | [Route], [HttpGet], [HttpPost] missing |
| **Usage** | ✅ Detected | HttpClient calls, axios, fetch, http.get() |
| **Registry** | ❌ Missing | No route registry |
| **Cross-File** | ❌ Not Used | Controllers in separate files not linked |
| **Method** | Single-Pass | Only detects usage |
| **Files** | All scanners | _scan_http_calls() in each |
| **Gap** | **CRITICAL** | Cannot link frontend calls to backend handlers |

**What's Missing:**
- C#: `[ApiController]`, `[Route("api/users")]`, `[HttpGet]`, `[HttpPost]`
- Express: `app.get()`, `app.post()`, `router.get()`
- Next.js: `/pages/api/*` route definitions
- GraphQL: Schema definitions and resolvers

---

### 3. COMPONENTS & PAGES - Status: PARTIAL (Definitions Present, Metadata Missing)

| Aspect | Status | Details |
|--------|--------|---------|
| **Definitions** | ✅ Detected | Component class/function names |
| **Usage** | ✅ Detected | UI triggers, event handlers |
| **Metadata** | ❌ Incomplete | Props, inputs, dependencies missing |
| **Registry** | ⚠️ Informal | Ad-hoc detection, no formal registry |
| **Cross-File** | ✅ Partial | XAML+CS loaded, TS+HTML loaded |
| **Method** | Single-Pass | Inline detection |
| **Files** | react_scanner.py, angular_scanner.py, wpf_scanner.py | Component detection methods |

**What's Partially Done:**
- React: `export function ComponentName` ✅, props definitions ❌
- Angular: `@Component` decorator ✅, @Input/@Output ❌
- WPF: `<Window x:Class>` ✅, dependency injection ❌

---

### 4. DEPENDENCIES - Status: NOT IMPLEMENTED

| Aspect | Status | Details |
|--------|--------|---------|
| **Definitions** | ❌ NOT Detected | Import, using, require statements |
| **Manifest** | ❌ NOT Parsed | package.json, .csproj not read |
| **Usage** | ❌ NOT Tracked | No correlation with detected operations |
| **Registry** | ❌ Missing | No dependency registry |
| **Cross-File** | ❌ Not Used | Can't link libraries to operations |
| **Method** | None | Not implemented |
| **Files** | N/A | Needs new implementation across all scanners |

**What's Missing:**
- JavaScript: `import axios from 'axios'`, `const fetch = require('fetch')`
- C#: `using System.Linq;`, `using Microsoft.EntityFrameworkCore;`
- Package manifests: `package.json`, `.csproj`, `requirements.txt`
- Library version tracking
- Dependency inheritance (transitive dependencies)

---

## Detection Method Comparison

### Single-Pass (Current for Most Operations)
```
File → Scan for Usage → Create Node → Done
```
**Problem:** Can't resolve references to definitions in other files

**Example:** Seeing `HttpClient.GetAsync("/api/users")` but don't know if that endpoint exists or has handlers

---

### Two-Pass (Current for Databases, Proposed for APIs/Dependencies)
```
First Pass:  All Files → Collect Definitions → Build Registry
Second Pass: All Files → Scan Usage → Resolve Against Registry → Link
```
**Benefit:** Cross-file linkage and completeness

**Example with Databases (Current):**
```
First Pass:  Find "class User { ... }" → Add to schemas_discovered
Second Pass: See "_context.Users" → Resolve "Users" → Link to User entity
```

**Example with APIs (Proposed):**
```
First Pass:  Find "[Route("api/users")] GET" → Add to routes_discovered
Second Pass: See "http.get('/api/users')" → Resolve "/api/users" → Link to controller
```

---

## Detection Location Matrix

```
┌─────────────────────────────────────────────────────────────────────┐
│ WORKFLOW TRACKER DETECTION LOCATIONS                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  builder.py (ORCHESTRATION)                                          │
│  ├─ _discover_schemas() ..................... FIRST PASS ✅ (DB)     │
│  ├─ _discover_routes() ...................... MISSING ❌ (API)      │
│  ├─ _discover_dependencies() ................ MISSING ❌             │
│  └─ _infer_workflow_edges() ................. SECONDARY PASS         │
│                                                                       │
│  csharp_scanner.py                                                    │
│  ├─ detect_schemas() ........................ FIRST PASS ✅           │
│  ├─ _scan_database_operations() ............. USES REGISTRY ✅        │
│  ├─ _scan_http_calls() ...................... INLINE, NO REGISTRY ❌  │
│  └─ (MISSING) detect_routes() ............... NEEDS IMPLEMENTATION    │
│  └─ (MISSING) detect_dependencies() ......... NEEDS IMPLEMENTATION    │
│                                                                       │
│  typescript_scanner.py                                                │
│  ├─ _scan_http_calls() ...................... INLINE, NO REGISTRY ❌  │
│  ├─ _scan_storage_operations() .............. INLINE                  │
│  └─ (MISSING) detect_routes() ............... NEEDS IMPLEMENTATION    │
│  └─ (MISSING) detect_dependencies() ......... NEEDS IMPLEMENTATION    │
│                                                                       │
│  react_scanner.py                                                     │
│  ├─ _detect_component_name() ................ INLINE ✅              │
│  ├─ _detect_url() ........................... INLINE ✅              │
│  ├─ _detect_http_calls() .................... INLINE, NO REGISTRY ❌  │
│  └─ (MISSING) detect_dependencies() ......... NEEDS IMPLEMENTATION    │
│                                                                       │
│  angular_scanner.py                                                   │
│  ├─ _detect_component_name() ................ INLINE ✅              │
│  ├─ _detect_ui_triggers_from_template() .... CROSS-FILE ✅          │
│  ├─ _detect_http_calls() .................... INLINE, NO REGISTRY ❌  │
│  └─ (MISSING) detect_dependencies() ......... NEEDS IMPLEMENTATION    │
│                                                                       │
│  wpf_scanner.py                                                       │
│  ├─ _detect_window_name() ................... INLINE ✅              │
│  ├─ _try_load_codebehind() .................. CROSS-FILE ✅          │
│  ├─ _detect_http_calls() .................... INLINE, NO REGISTRY ❌  │
│  └─ (MISSING) detect_dependencies() ......... NEEDS IMPLEMENTATION    │
│                                                                       │
│  models.py (DATA STRUCTURES)                                          │
│  ├─ WorkflowGraph ........................... PRESENT ✅              │
│  ├─ WorkflowNode ............................ PRESENT ✅              │
│  ├─ TableSchema ............................. PRESENT ✅              │
│  ├─ ScanResult.schemas_discovered ........... PRESENT ✅              │
│  ├─ (MISSING) RouteDefinition ............... NEEDS IMPLEMENTATION    │
│  └─ (MISSING) DependencyDefinition .......... NEEDS IMPLEMENTATION    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Information Captured Per Entity Type

### Database Entities
```python
TableSchema(
    entity_name="User",           # e.g., User class
    table_name="Users",           # e.g., DbSet<User> Users property
    file_path="/path/to/User.cs",
    line_number=42,
    properties=["Id", "Name", "Email"],
    dbset_name="Users",
    metadata={
        'source': 'Entity',
        'has_table_attribute': True
    }
)
```

### API Calls (Currently Detected)
```python
WorkflowNode(
    id="file.cs:api:123",
    type=WorkflowType.API_CALL,
    name="API Call: GET",
    endpoint="/api/users",
    method="GET",
    location=CodeLocation("file.cs", 123),
    code_snippet="http.GetAsync('/api/users')",
    metadata={'library': 'HttpClient'}
)
```

### API Routes (NOT Currently Detected - Proposed)
```python
RouteDefinition(
    endpoint="/api/users",
    method="GET",
    handler_method="GetUsers",
    controller_name="UsersController",
    file_path="/path/to/UsersController.cs",
    line_number=42,
    parameters=[],
    return_type="IActionResult",
    metadata={'framework': '.NET Core'}
)
```

### Dependencies (NOT Currently Detected - Proposed)
```python
DependencyDefinition(
    package_name="Entity Framework Core",
    package_type="nuget",
    version="7.0.0",
    files_using=["file1.cs", "file2.cs"],
    usage_frequency=15,
    detection_type="using_statement",
    declared_in="file.csproj",
    metadata={'category': 'database_orm'}
)
```

### Components
```python
WorkflowNode(
    id="Component.tsx:ui_trigger:42",
    type=WorkflowType.DATA_TRANSFORM,  # Placeholder for UI events
    name="UI: Click",
    description="User interaction in UserComponent",
    location=CodeLocation("Component.tsx", 42),
    metadata={
        'trigger_type': 'ui_click',
        'component': 'UserComponent',
        'handler': 'handleDelete',
        'is_ui_trigger': True
    }
)
```

---

## Why Two-Pass Approach Works for Databases

### The Problem It Solves

In a typical C# application:
```
Data Layer/
├─ Models/
│  ├─ User.cs          # Entity class defined here
│  ├─ Order.cs         # Entity class defined here
│  └─ Product.cs       # Entity class defined here
├─ DbContext.cs        # DbSet properties here
└─ Repositories/
   ├─ UserRepository.cs # Uses _context.Users (references User entity by name)
   ├─ OrderRepository.cs # Uses _context.Orders
   └─ ProductRepository.cs # Uses _context.Products
```

**Issue:** When you see `_context.Users.Where(...)`:
- You find the string "Users"
- But you need to know: Is there a DbSet<Users>? An entity class called User? A table called Users?

**Two-Pass Solution:**
1. **First Pass:** Scan all files, find all DbSet properties and entity classes, build a map:
   ```
   {
     "Users": TableSchema(entity_name="User", table_name="Users", ...),
     "User": TableSchema(entity_name="User", table_name="Users", ...),
     "Orders": TableSchema(entity_name="Order", table_name="Orders", ...),
     ...
   }
   ```

2. **Second Pass:** When you see `_context.Users`, look it up in the map → resolved!

---

## Same Pattern Would Help APIs

### Current Single-Pass Problem

```
Frontend/
├─ pages/
│  ├─ UserProfile.tsx     # Has axios.get('/api/users/123')
│  └─ AdminPanel.tsx      # Has http.get('/admin/users')

Backend/
├─ Controllers/
│  ├─ UsersController.cs  # Has [Route("api/users")] [HttpGet("{id}")]
│  └─ AdminController.cs  # Has [Route("admin/users")] [HttpGet()]
```

**Current Issue:**
- Scanner finds `axios.get('/api/users/123')` ✅
- Scanner finds `axios.get('/admin/users')` ✅
- **But:** Scanner finds NO `[Route("api/users")]` definitions ❌
- **Result:** You know what frontend calls but not if endpoints exist

**Two-Pass Solution:**
1. **First Pass:** Find all route definitions
   ```
   {
     "/api/users": {method: "GET", handler: "GetUsers", file: "UsersController.cs", ...},
     "/api/users/{id}": {method: "GET", handler: "GetUserById", ...},
     "/admin/users": {method: "GET", handler: "GetAdminUsers", ...},
   }
   ```

2. **Second Pass:** When you find `axios.get('/api/users/123')`:
   - Recognize it matches route "/api/users/{id}"
   - Link it to GetUserById handler
   - Create edge: UI Trigger → API Route → Backend Handler

---

## Quick Implementation Checklist

### For API Routes (Two-Pass)
- [ ] Add `RouteDefinition` dataclass to models.py
- [ ] Add `detect_routes()` method to csharp_scanner.py (detect [Route], [HttpGet], etc.)
- [ ] Add `detect_routes()` method to typescript_scanner.py (detect Express routes, Next.js routes)
- [ ] Add `_discover_routes()` method to builder.py (first pass, builds registry)
- [ ] Modify `_scan_http_calls()` to use `route_registry` parameter
- [ ] Update `scan()` method in builder.py to call `_discover_routes()`

### For Dependencies (Two-Pass)
- [ ] Add `DependencyDefinition` dataclass to models.py
- [ ] Add `detect_dependencies()` method to base.py (abstract)
- [ ] Implement `detect_dependencies()` in each scanner
- [ ] Add package manifest parsing (package.json, .csproj, etc.)
- [ ] Add `_discover_dependencies()` method to builder.py (first pass)
- [ ] Modify workflow nodes to include dependency metadata
- [ ] Create edges linking workflows to their dependencies

### For Component Registry (Formalization)
- [ ] Add `ComponentDefinition` dataclass to models.py
- [ ] Create `components_discovered` registry in ScanResult
- [ ] Add `detect_components()` method to UI scanners
- [ ] Build formal component registry in `_discover_components()` in builder.py
- [ ] Add component metadata: props, inputs, outputs, dependencies

---

## Performance Implications

### Current Database Schema Discovery (Two-Pass)
- First Pass: Scans ~X files, finds ~100 entities, creates registry
- Second Pass: Scans all files, resolves entities via O(1) registry lookup
- **Total Time:** ~T seconds for database operations

### Proposed API Route Discovery (Two-Pass)
- First Pass: Scans C# files for [Route], [HttpGet], etc. (~similar cost to schema discovery)
- Second Pass: When finding API calls, O(1) route registry lookup
- **Additional Time:** ~0.5T seconds (only scanning controllers for routes)
- **Benefit:** Can skip endpoint validation, complete API mapping

### Proposed Dependency Discovery (Two-Pass)
- First Pass: Parse all imports/using statements + manifest files
- **Additional Time:** ~0.2T seconds
- **Benefit:** Can annotate workflows with dependency info

### Overall Impact
- **Schema Discovery (Current):** ~T seconds (needed)
- **API Routes (Proposed):** +0.5T seconds
- **Dependencies (Proposed):** +0.2T seconds
- **Total:** ~1.7T seconds vs current 1.0T (70% increase, but highly parallelizable)

---

## Success Metrics After Implementation

### Today (Before Enhancement)
```
Detected:
✅ Database operations (reads/writes)
✅ API calls (from frontend to backend)
✅ UI triggers (clicks, submits)
✅ Message queue operations

Cannot Trace:
❌ Which frontend calls match which backend endpoints
❌ Which external libraries are involved
❌ Unused API routes or handlers
❌ Endpoint-to-handler mappings
```

### After Enhancement
```
Detected:
✅ Database operations (reads/writes)
✅ API routes and handlers
✅ API calls (frontend to backend)
✅ Full end-to-end request paths
✅ UI triggers → Handler → Database
✅ External dependencies per operation
✅ Unused routes and handlers
✅ API mismatches

Can Now Trace:
✅ Frontend call "GET /api/users" → Handler "GetUsers()" → Database "Users"
✅ Dependencies: axios → HttpClient → Entity Framework → SQL Server
✅ Which external packages handle which operations
✅ Complete workflow from UI to database
```

---

