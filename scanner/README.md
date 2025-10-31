# Pinata Code - Scanning Engine

This directory contains the existing Python scanning engine that analyzes codebases to extract workflows, database operations, and data flows.

## Overview

The scanning engine is a **standalone Python package** that performs static code analysis on repositories. It is designed to be imported and used by the backend FastAPI application.

## Structure

```
scanner/
├── __init__.py           # Package initialization
├── models.py             # Data models (ScanResult, Node, Edge)
├── config_loader.py      # Configuration loading
├── scanner/              # Core scanning logic
│   ├── analyzer.py       # Main analysis orchestrator
│   ├── csharp_scanner.py # C# code scanner
│   ├── ts_scanner.py     # TypeScript scanner
│   └── pattern_matcher.py # Pattern matching utilities
├── graph/                # Graph generation
│   ├── builder.py        # Workflow graph builder
│   └── renderer.py       # Mermaid/HTML rendering
├── integrations/         # External integrations
│   ├── confluence.py     # Confluence publishing
│   └── export.py         # Export utilities
├── cli/                  # CLI interface (legacy)
│   ├── main.py           # CLI entry point
│   └── streamlit_app.py  # Streamlit GUI
└── tests/                # Test suite

```

## Key Components

### 1. Scanner Engine
- **Language Scanners**: Analyze code in C#, TypeScript, JavaScript, etc.
- **Pattern Matching**: Detect data operations (CRUD, queries, API calls)
- **Graph Building**: Construct workflow graphs from detected operations

### 2. Data Models
```python
from scanner.models import ScanResult, Node, Edge

# Main result object
class ScanResult:
    repository: str
    files_scanned: int
    nodes_found: int
    nodes: List[Node]
    edges: List[Edge]
    metadata: dict
```

### 3. Integration Points

**Used by Backend API**:
```python
from scanner.scanner.analyzer import analyze_repository
from scanner.models import ScanResult

# Scan a repository
result: ScanResult = analyze_repository(
    repo_path="/path/to/repo",
    file_extensions=[".cs", ".ts"],
    progress_callback=lambda current, total, msg: print(msg)
)
```

## Features

### Current Capabilities
- ✅ Static code analysis (no runtime execution required)
- ✅ Multi-language support (C#, TypeScript, JavaScript)
- ✅ Workflow graph generation
- ✅ Database schema analysis from model files
- ✅ API endpoint detection
- ✅ Mermaid diagram generation
- ✅ Confluence integration
- ✅ Progress tracking with callbacks

### Planned Enhancements (Phase 2)
- [ ] **Incremental scanning**: Only scan changed files
- [ ] **File-level caching**: Redis cache for file scan results
- [ ] **Performance optimization**: Compiled regex, memory-mapped files
- [ ] **Enhanced language support**: Python, Java, Go
- [ ] **Relationship inference**: Smarter detection of data flows
- [ ] **Plugin architecture**: Extensible scanner framework

## Usage

### As a Library (Backend Integration)

```python
from scanner.scanner.analyzer import analyze_repository
from scanner.graph.builder import build_workflow_graph
from scanner.graph.renderer import render_mermaid

# 1. Scan repository
result = analyze_repository(
    repo_path="/path/to/repo",
    file_extensions=[".cs", ".ts", ".js"]
)

# 2. Build graph
graph = build_workflow_graph(result)

# 3. Render diagram
mermaid_code = render_mermaid(graph)
```

### As CLI (Legacy)

```bash
# Scan repository
python -m scanner.cli.main /path/to/repo --output ./results

# Run Streamlit GUI
streamlit run scanner/cli/streamlit_app.py
```

## Configuration

The scanner uses configuration from environment variables or YAML files:

```python
# Environment variables
MAX_FILE_SIZE=10485760  # 10MB
FILE_EXTENSIONS=.cs,.ts,.js
SCAN_TIMEOUT=3600

# Or config file
scanner_config = {
    'file_extensions': ['.cs', '.ts'],
    'max_file_size': 10 * 1024 * 1024,
    'exclude_patterns': ['**/node_modules/**', '**/bin/**']
}
```

## Testing

```bash
# Run scanner tests
cd scanner
pytest tests/ -v

# With coverage
pytest tests/ --cov=scanner --cov-report=html
```

## Performance

**Current Performance** (based on real-world testing):
- **9,161 files**: ~45 seconds
- **31,587 nodes**: Successfully processed
- **Memory usage**: ~500MB for large repos

**Target Performance** (with Phase 2 optimizations):
- **Initial scan**: Same (~45s for 9K files)
- **Incremental scan**: <5s (only changed files)
- **Cache hit rate**: 80%+ on repeat scans
- **Memory usage**: <300MB with streaming

## Migration Notes

This code was previously located in `src/`. It has been moved to `scanner/` as part of the monorepo restructuring for the production SaaS platform.

**Backward Compatibility**:
- Existing imports still work via symlinks
- CLI tools remain functional
- Streamlit GUI still accessible

**Future Changes**:
- Scanner will become a service called by FastAPI backend
- Results will be cached in Redis and stored in S3
- Scans will run as Celery background jobs

## Development

### Adding a New Language Scanner

1. Create scanner module:
```python
# scanner/scanner/python_scanner.py
from .base_scanner import BaseScanner

class PythonScanner(BaseScanner):
    def scan(self, file_path: str) -> List[Node]:
        # Implement Python-specific scanning
        pass
```

2. Register in analyzer:
```python
# scanner/scanner/analyzer.py
SCANNERS = {
    '.cs': CSharpScanner,
    '.ts': TypeScriptScanner,
    '.py': PythonScanner,  # Add new scanner
}
```

### Adding New Detection Patterns

```python
# scanner/scanner/pattern_matcher.py
PATTERNS = {
    'database_read': r'\.Find\(|\.FirstOrDefault\(|\.Where\(',
    'database_write': r'\.Add\(|\.Update\(|\.Remove\(',
    # Add new patterns here
}
```

## License

Part of Pinata Code - Proprietary Software
