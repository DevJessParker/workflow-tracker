# Entity Detection Analysis: Current State Beyond Database Operations

## Executive Summary

The workflow tracker currently detects **entities beyond database operations**, but with varying levels of sophistication and structure. The system has implemented a **two-pass schema discovery approach for databases** (first pass: schema discovery, second pass: usage detection), which has proven successful. This analysis identifies similar opportunities for upfront discovery in other entity types.

---

## 1. API Routes/Endpoints Detection

### Current Detection Status: PRESENT (Single-Pass, Inline)

#### C# Scanner (`csharp_scanner.py`)
**Detection Method:** Inline during main scan
- **Location:** `_scan_http_calls()` method
- **Patterns Detected:**
  - HttpClient instantiation and methods
  - GetAsync, PostAsync, PutAsync, DeleteAsync, SendAsync
- **Information Captured:**
  - HTTP method (GET, POST, PUT, DELETE)
  - Endpoint URL (extracted from string literals)
  - Code location and snippet
  - Metadata: library type

```python
HTTP_PATTERNS = [
    r'HttpClient',
    r'\.GetAsync\s*\(',
    r'\.PostAsync\s*\(',
    r'\.PutAsync\s*\(',
    r'\.DeleteAsync\s*\(',
    r'\.SendAsync\s*\(',
]
```

**Limitation:** No detection of API route definitions (@Route, [HttpGet], [HttpPost] on controllers)

---

#### TypeScript/Angular Scanner (`typescript_scanner.py`)
**Detection Method:** Inline during main scan
- **Location:** `_scan_http_calls()` method
- **Patterns Detected:**
  - Angular HttpClient (http.get, http.post, http.put, http.delete, http.patch)
  - Fetch API
  - Axios calls
- **Information Captured:**
  - HTTP method
  - Endpoint URL
  - Code location and snippet
  - Library type (fetch, axios, HttpClient)

```python
HTTP_PATTERNS = [
    r'http\.get',
    r'http\.post',
    r'http\.put',
    r'http\.delete',
    r'http\.patch',
    r'fetch\s*\(',
    r'axios\.',
]
```

**Limitation:** No detection of route/endpoint definitions (Next.js pages, API routes, Express.js routes)

---

#### Angular Scanner (`angular_scanner.py`)
**Detection Method:** Inline during main scan
- **Location:** `_detect_http_calls()` method
- **Patterns Detected:**
  - `this.http.get/post/put/delete/patch` with typed and untyped patterns
- **Information Captured:**
  - HTTP method (hard-coded per pattern)
  - Endpoint URL (first capture group)
  - Code location and snippet
  - Metadata: library='HttpClient', framework='Angular'

```python
HTTP_PATTERNS = [
    (r'this\.http\.get\s*<[^>]+>\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'GET'),
    (r'this\.http\.post\s*<[^>]+>\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'POST'),
    # ... etc
]
```

**Limitation:** No detection of Angular route definitions (@Injectable decorators on services)

---

#### React Scanner (`react_scanner.py`)
**Detection Method:** Inline during main scan
- **Location:** `_detect_http_calls()` method
- **Patterns Detected:**
  - Fetch with URL and optional method
  - Axios with method
  - http client calls (Angular-style)
- **Information Captured:**
  - HTTP method (extracted or defaulted to GET)
  - Endpoint URL
  - Code location
  - Metadata: library type, is_frontend_call=true
  - **Also detects:** Route definitions and component routing

```python
HTTP_PATTERNS = [
    (r'fetch\s*\(\s*[\'"]([^\'"]+)[\'"](?:.*?method\s*:\s*[\'"](\w+)[\'"])?', 'fetch'),
    (r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', 'axios'),
    (r'http\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', 'http'),
]

ROUTE_PATTERNS = [
    r'<Route\s+path\s*=\s*[\'"]([^\'"]+)[\'"]',
    r'path\s*:\s*[\'"]([^\'"]+)[\'"]',
    r'href\s*=\s*[\'"]([^\'"]+)[\'"]',
]
```

---

#### WPF Scanner (`wpf_scanner.py`)
**Detection Method:** Inline during main scan
- **Location:** `_detect_http_calls()` method
- **Patterns Detected:**
  - HttpClient instantiation
  - WebClient usage
  - GetAsync, PostAsync, DownloadString, UploadString
- **Information Captured:**
  - HTTP method (GET, POST)
  - Endpoint URL
  - Code location and snippet
  - Metadata: library='HttpClient/WebClient', framework='WPF'

---

### Missing: Controller/Route Definitions

**Not Currently Detected:**
- C# controller attributes: `[ApiController]`, `[Route("api/...")]`, `[HttpGet]`, `[HttpPost]`
- Express.js routes: `app.get()`, `app.post()`
- Next.js API routes in `/pages/api/`
- GraphQL endpoint definitions

### Analysis: Would Two-Pass Approach Help?

**YES - Significantly**

1. **First Pass - Route Discovery:**
   - Scan for all controller/route definitions across the codebase
   - Build a registry: `{endpoint: {method, handler_method, file_location}}`
   - Handle frameworks: .NET Core, Express, Next.js, GraphQL

2. **Second Pass - Route Usage:**
   - When detecting API calls, resolve them against the route registry
   - Link frontend calls to backend handlers
   - Create edges showing full request path

**Benefits:**
- Complete API surface mapping
- Better handler-to-endpoint mapping
- Detect unused routes and dead code
- Identify API mismatches (calling `/api/users/list` when endpoint is `/api/users`)

---

## 2. Components & Pages Detection

### Current Detection Status: PARTIAL (Single-Pass, Inline)

#### React Scanner (`react_scanner.py`)
**Detection Method:** Inline during scan
- **Location:** `_detect_component_name()`, `_detect_url()` methods
- **Component Detection:**
  - Export statements: `export function ComponentName`
  - Export default patterns
  - Fallback to filename
- **Route Detection:**
  - `<Route path="...">` patterns
  - Path definitions in objects
  - Href attributes
- **Information Captured:**
  - Component name
  - Component URL/route
  - Code location
  - UI event handlers (onClick, onSubmit, onChange, onLoad)
  - HTTP calls within component

```python
COMPONENT_PATTERNS = [
    r'export\s+(?:default\s+)?(?:function|const)\s+(\w+)',
    r'const\s+(\w+)\s*[=:]\s*\([^)]*\)\s*(?:=>|:)',
    r'function\s+(\w+)\s*\([^)]*\)',
]

ROUTE_PATTERNS = [
    r'<Route\s+path\s*=\s*[\'"]([^\'"]+)[\'"]',
    r'path\s*:\s*[\'"]([^\'"]+)[\'"]',
    r'href\s*=\s*[\'"]([^\'"]+)[\'"]',
]
```

**Detection Granularity:**
- Component → UI Triggers → HTTP Calls
- Creates edges between triggers and HTTP calls within ~50 line proximity

---

#### Angular Scanner (`angular_scanner.py`)
**Detection Method:** Multi-file (TypeScript + Template)
- **Location:** `_detect_component_name()`, `_try_load_template()`, `_detect_ui_triggers_from_template()`
- **Component Detection:**
  - `@Component` decorator with selector
  - Class inheritance from Component
  - Filename-based fallback
- **Route Detection:**
  - Path definitions in routing config
  - RouterModule patterns
  - this.router.navigate calls
- **UI Event Detection:**
  - Angular event bindings: `(click)`, `(submit)`, `(change)`, `(input)`, `(keyup)`, etc.
  - Loads associated HTML template to find event bindings
- **Information Captured:**
  - Component name (from selector or class)
  - Component URL/route
  - Event handlers
  - HTTP calls
  - Associated template file
  - Framework metadata

```python
COMPONENT_PATTERNS = [
    r'@Component\s*\(\s*\{[^}]*selector\s*:\s*[\'"]([^\'"]+)[\'"]',
    r'export\s+class\s+(\w+)Component',
]

EVENT_HANDLER_PATTERNS = [
    (r'\(click\)\s*=\s*"([^"]+)"', 'ui_click'),
    (r'\(submit\)\s*=\s*"([^"]+)"', 'ui_submit'),
    (r'\(ngSubmit\)\s*=\s*"([^"]+)"', 'ui_submit'),
    (r'\(change\)\s*=\s*"([^"]+)"', 'ui_change'),
    (r'\(input\)\s*=\s*"([^"]+)"', 'ui_change'),
    (r'\(mousedown\)\s*=\s*"([^"]+)"', 'ui_click'),
    (r'\(keyup\)\s*=\s*"([^"]+)"', 'ui_keypress'),
]
```

---

#### WPF Scanner (`wpf_scanner.py`)
**Detection Method:** Dual-file (XAML + Code-Behind)
- **Location:** `_detect_window_name()`, `_try_load_codebehind()`, `_detect_event_handler_methods()`
- **Window/Page Detection:**
  - `<Window x:Class="...">` XAML attribute
  - `<Page x:Class="...">` XAML attribute
  - `<UserControl x:Class="...">` XAML attribute
  - Class inheritance: `public partial class X : Window`
  - Filename-based fallback
- **UI Event Detection (XAML):**
  - `Click="..."`, `SelectionChanged="..."`, `TextChanged="..."`, `KeyDown="..."`, `Loaded="..."`
  - Matches handler names to code-behind methods
- **Event Handler Detection (C#):**
  - Method signature matching: `private void MethodName(object sender, EventArgs e)`
  - Async event handlers
- **Information Captured:**
  - Window/Page/UserControl name
  - Event handler names
  - HTTP calls in code-behind
  - File associations (XAML ↔ CS)

```python
XAML_EVENT_PATTERNS = [
    (r'Click\s*=\s*"([^"]+)"', 'ui_click'),
    (r'SelectionChanged\s*=\s*"([^"]+)"', 'ui_change'),
    (r'TextChanged\s*=\s*"([^"]+)"', 'ui_change'),
    (r'KeyDown\s*=\s*"([^"]+)"', 'ui_keypress'),
    (r'Loaded\s*=\s*"([^"]+)"', 'page_load'),
    # ...
]

WINDOW_PATTERNS = [
    r'<Window\s+x:Class\s*=\s*"([^"]+)"',
    r'<Page\s+x:Class\s*=\s*"([^"]+)"',
    r'<UserControl\s+x:Class\s*=\s*"([^"]+)"',
    r'public\s+partial\s+class\s+(\w+)\s*:\s*Window',
    r'public\s+partial\s+class\s+(\w+)\s*:\s*Page',
    r'public\s+partial\s+class\s+(\w+)\s*:\s*UserControl',
]
```

---

### Missing: Component/Page Details

**Not Currently Detected:**
- Props/Input parameters (React, Angular)
- Component state definitions
- Lifecycle hooks (React, Angular)
- Service dependencies (Angular @Injectable)
- Layout/Style imports
- TypeScript interface/type definitions
- Navigation parameters
- Page-level metadata (title, description, SEO)

### Analysis: Would Two-Pass Approach Help?

**YES - Moderately**

1. **First Pass - Component/Page Registry:**
   - Identify all component/page definitions
   - Extract metadata: props, inputs, dependencies
   - Build component tree
   - Map routes to components
   - Identify which services are injected

2. **Second Pass - Usage Analysis:**
   - Detect component imports and usage
   - Link components to routes
   - Identify unused components
   - Map service dependencies to implementations

**Benefits:**
- Complete component inventory
- Better understanding of component tree
- Dependency injection visualization
- Detection of unused components
- Better route-to-component mapping

**Current State:** Already doing multi-file correlation (Angular XAML+CS, WPF XAML+CS), but could be formalized

---

## 3. Dependencies Detection

### Current Detection Status: NOT IMPLEMENTED

**None of the scanners currently detect:**
- Import statements (JavaScript: `import`, `require`)
- Using statements (C#: `using`)
- Package dependencies (package.json, .csproj)
- NuGet packages
- npm packages
- Service registrations (C# DI containers)

---

### Analysis: Why This Matters

Understanding dependencies is crucial for:
1. **Workflow Completeness:** Knowing which libraries are used (e.g., Entity Framework, axios, RxJS)
2. **Data Flow Tracking:** Understanding what packages handle data operations
3. **Risk Assessment:** Identifying external dependencies in workflows
4. **Performance Analysis:** Understanding the call stack through libraries

---

### Recommendation: Two-Pass Approach

**First Pass - Dependency Discovery:**
1. Scan all files for import/using statements
2. Parse package manifest files (package.json, .csproj, requirements.txt)
3. Build dependency registry:
   ```
   {
     "package_name": {
       "version": "1.0.0",
       "type": "npm|nuget|pip",
       "files_using": [...],
       "frequency": 5
     }
   }
   ```

**Second Pass - Dependency Usage:**
1. When detecting workflows, annotate with dependency information
2. Link API calls to HTTP libraries (axios, HttpClient, fetch)
3. Link database calls to ORM libraries (Entity Framework, TypeORM, etc.)
4. Create edges showing dependency resolution

**Implementation Locations:**
- `base.py`: Add `detect_dependencies()` abstract method
- `csharp_scanner.py`: Parse `using` statements, `.csproj` files
- `typescript_scanner.py`: Parse `import` statements, `package.json`
- `builder.py`: First pass discovery (like database schemas)

---

## Comparative Analysis: Current vs. Two-Pass Approach

| Entity Type | Current Status | Detection Type | Detects Definition | Detects Usage | Needs 2-Pass | Priority |
|---|---|---|---|---|---|---|
| **Database Tables** | ✅ Complete | Two-pass | ✅ Yes | ✅ Yes | N/A | - |
| **API Routes** | ❌ Incomplete | Single-pass | ❌ No | ✅ Yes | ✅ HIGH | 🔴 |
| **Components** | ✅ Partial | Single-pass | ✅ Yes | ✅ Yes | ⚠️ Medium | 🟡 |
| **Dependencies** | ❌ Missing | None | ❌ No | ❌ No | ✅ HIGH | 🔴 |
| **Routes/Pages** | ✅ Partial | Single-pass | ✅ Yes | ✅ Inline | ⚠️ Medium | 🟡 |

---

## Schema vs. API Routes: Implementation Pattern Comparison

### Database Schemas (Current Two-Pass Implementation)

**First Pass - `_discover_schemas()`:**
```python
# In builder.py
schemas = csharp_scanner.detect_schemas(file_path)  # Look for DbSet, [Table], entity classes
result.schemas_discovered[schema.entity_name] = schema
```

**Second Pass - Usage:**
```python
# In csharp_scanner.py scan_file()
file_graph = scanner.scan_file(file_path, schema_registry=result.schemas_discovered)
table_name = self._extract_table_name(line, lines, i)  # Uses registry to resolve entity → table
```

**Why This Works:**
- Entity definitions are scattered (DbContext in one file, entity classes in many files)
- References are by entity name (e.g., `_context.Users`) not table name
- Registry resolves entity name → table name mapping

---

### API Routes (Proposed Two-Pass Implementation)

**First Pass - Route Discovery (NEW):**
```python
# In csharp_scanner.py (new method)
def detect_routes(self, file_path: str) -> List[RouteDefinition]:
    # Look for [Route], [HttpGet], [HttpPost] attributes
    # Look for controller class definitions
    # Build: {endpoint: {method, handler_method, file}}

# In typescript_scanner.py (new method)
def detect_routes(self, file_path: str) -> List[RouteDefinition]:
    # Look for Express app.get(), app.post(), etc.
    # Look for Next.js pages in /pages/api/
    # Build: {endpoint: {method, handler, file}}
```

**Second Pass - Route Usage:**
```python
# In builder.py
self._discover_routes(files_to_scan, result)  # First pass

# Then in scan_file()
file_graph = scanner.scan_file(file_path, route_registry=result.routes_discovered)
# When detecting API call to "/api/users", can resolve to handler method
```

**Benefits Over Current:**
- Complete API surface mapping
- Can link frontend calls to backend handlers
- Detect unused routes
- Identify handler → HTTP method mismatches

---

## File Structure Impact

### Current Detection in Scanner Files

```
scanner/
├── scanner/
│   ├── base.py
│   │   └── should_detect_type() - Configuration checking
│   ├── csharp_scanner.py
│   │   ├── detect_schemas() ✅ - DbSet and [Table] detection
│   │   ├── _scan_database_operations() - Inline, uses schema_registry
│   │   ├── _scan_http_calls() - Detects usage only
│   │   └── _scan_message_queues() - Inline detection
│   ├── typescript_scanner.py
│   │   ├── _scan_http_calls() - Inline detection
│   │   ├── _scan_storage_operations() - Cache/storage operations
│   │   └── _scan_data_transforms() - RxJS operators
│   ├── react_scanner.py
│   │   ├── _detect_component_name() - Component definition
│   │   ├── _detect_url() - Route definition
│   │   ├── _detect_ui_triggers() - UI event detection
│   │   └── _detect_http_calls() - HTTP call detection
│   ├── angular_scanner.py
│   │   ├── _detect_component_name() - @Component decorator
│   │   ├── _detect_url() - Route definition
│   │   ├── _detect_ui_triggers_from_template() - Template event binding
│   │   └── _detect_http_calls() - HTTP call detection
│   └── wpf_scanner.py
│       ├── _detect_window_name() - Window definition
│       ├── _try_load_codebehind() - Multi-file loading
│       ├── _detect_ui_triggers_from_xaml() - Event binding
│       └── _detect_http_calls() - HTTP call detection
└── graph/
    └── builder.py
        ├── _discover_schemas() - First-pass schema discovery
        ├── build() - Main orchestration
        └── _infer_workflow_edges() - Edge creation
```

---

## Recommendations Summary

### Immediate (High Priority)

1. **API Route Discovery (Two-Pass)**
   - Add `detect_routes()` method to C# and TypeScript scanners
   - Implement first-pass route discovery in `builder.py._discover_routes()`
   - Link frontend API calls to backend handlers
   - Files to modify:
     - `csharp_scanner.py`: Add route detection
     - `typescript_scanner.py`: Add route detection  
     - `builder.py`: Add `_discover_routes()` pass
     - `models.py`: Add `RouteDefinition` dataclass

2. **Dependency Detection (Two-Pass)**
   - Add `detect_dependencies()` method to all scanners
   - Scan manifest files (package.json, .csproj)
   - Implement first-pass dependency discovery
   - Link workflows to their dependent libraries
   - Files to modify:
     - All scanners: Add dependency detection
     - `models.py`: Add `DependencyDefinition` dataclass
     - `builder.py`: Add `_discover_dependencies()` pass

### Medium Priority (Enhancement)

1. **Component/Page Registry Formalization**
   - Currently done ad-hoc, formalize into registry
   - Extract component metadata (props, inputs, outputs)
   - Build component dependency tree
   - Implementation: Add formal registry in `builder.py`

2. **Expand Component Detection**
   - Add TypeScript interface detection
   - Detect props/input definitions
   - Track component nesting

### Lower Priority (Future)

1. **Service/Interface Detection**
   - Map service interfaces to implementations
   - Track DI container registrations

2. **Type Definition Tracking**
   - Understand data types flowing through workflows
   - Build type compatibility matrix

---

## Code Quality Observations

### Strengths
- Clear separation of concerns (base class, scanner implementations)
- Consistent pattern recognition approach (regex-based)
- Good use of code location tracking
- Schema registry pattern is reusable and effective
- Multi-file support (XAML+CS, TS+HTML templates)

### Areas for Improvement
- No dependency detection infrastructure
- Route/endpoint definitions completely missed
- Ad-hoc component tracking (not formalized)
- Limited type system awareness
- No cross-file type resolution (TypeScript/Angular interfaces)

---

## Impact Analysis

### If Two-Pass Approach Adopted for APIs and Dependencies

**Currently Detected Workflows:**
```
API Call → (endpoint URL) → HTTP Call Node
Database Read/Write → (table name) → Database Node
UI Event → (handler name) → Event Handler Node
```

**With Two-Pass Enhancement:**
```
UI Event → Handler Method → HTTP Call → API Route Definition → Backend Handler → Database Operation

Dependency: axios → Frontend API Call
Dependency: HttpClient → Backend API Call
Dependency: Entity Framework → Database Operation
```

**Actionable Insights Gained:**
- Full end-to-end request tracing
- Unused API routes/handlers
- Orphaned database tables (no handlers)
- Outdated client-side endpoint calls
- Missing or duplicate API definitions
- Unused library dependencies

---

## Conclusion

The workflow tracker has successfully implemented a **two-pass discovery approach for database entities**, proving the effectiveness of this pattern. The same approach would significantly improve:

1. **API Route Detection** - Currently missing route definitions
2. **Dependency Tracking** - Currently completely absent
3. **Component Metadata** - Currently ad-hoc and informal

These three areas are the most critical gaps in the current entity detection system and would directly improve workflow traceability and completeness of visualization.

**Estimated Implementation Effort:**
- API Routes: 6-8 hours (two-pass framework already exists)
- Dependencies: 8-10 hours (new infrastructure)
- Component Formalization: 3-4 hours (refactor existing code)

