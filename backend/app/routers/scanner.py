"""
Scanner API Router
Handles repository scanning, analysis, and visualization endpoints
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import os
import sys

# Add scanner to path
sys.path.insert(0, '/scanner')

from graph.builder import WorkflowGraphBuilder
from graph.renderer import WorkflowRenderer

router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])


class RepoSourceType(str, Enum):
    """Repository source types"""
    LOCAL = "local"
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class ScanRequest(BaseModel):
    """Request model for starting a scan"""
    repo_path: str = Field(..., description="Path to repository (local or URL)")
    source_type: RepoSourceType = Field(default=RepoSourceType.LOCAL, description="Repository source type")
    file_extensions: List[str] = Field(default=[".cs", ".ts", ".js"], description="File extensions to scan")
    detect_database: bool = Field(default=True, description="Detect database operations")
    detect_api: bool = Field(default=True, description="Detect API calls")
    detect_files: bool = Field(default=True, description="Detect file I/O")
    detect_messages: bool = Field(default=True, description="Detect message queues")
    detect_transforms: bool = Field(default=True, description="Detect data transforms")
    organization_id: Optional[str] = Field(default=None, description="Organization ID (for cloud repos)")


class ScanResponse(BaseModel):
    """Response model for scan results"""
    scan_id: str
    status: str
    message: str
    files_scanned: Optional[int] = None
    nodes_found: Optional[int] = None
    edges_found: Optional[int] = None


class ScanStatus(BaseModel):
    """Scan status model"""
    scan_id: str
    status: str
    progress: float
    message: str
    files_scanned: int
    nodes_found: int
    eta: Optional[str] = None
    total_files: Optional[int] = None


# In-memory storage for scan results (replace with Redis/DB in production)
SCAN_RESULTS = {}
SCAN_STATUS = {}


@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Start a new repository scan

    - **repo_path**: Path to repository (local directory or GitHub URL)
    - **source_type**: Type of repository source (local, github, gitlab, bitbucket)
    - **file_extensions**: List of file extensions to scan
    - **detect_***: Various detection options
    """
    import uuid
    scan_id = str(uuid.uuid4())

    # Validate repository path
    if request.source_type == RepoSourceType.LOCAL:
        if not os.path.exists(request.repo_path):
            raise HTTPException(status_code=404, detail=f"Repository path not found: {request.repo_path}")

    # Initialize scan status
    SCAN_STATUS[scan_id] = {
        "scan_id": scan_id,
        "status": "queued",
        "progress": 0.0,
        "message": "Scan queued",
        "files_scanned": 0,
        "nodes_found": 0,
        "eta": None,
        "total_files": None
    }

    # Queue the scan as a background task
    background_tasks.add_task(
        run_scan,
        scan_id=scan_id,
        request=request
    )

    return ScanResponse(
        scan_id=scan_id,
        status="queued",
        message="Scan started successfully"
    )


@router.get("/scan/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    """Get the status of a running scan"""
    if scan_id not in SCAN_STATUS:
        raise HTTPException(status_code=404, detail="Scan not found")

    return SCAN_STATUS[scan_id]


@router.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get the results of a completed scan"""
    if scan_id not in SCAN_RESULTS:
        raise HTTPException(status_code=404, detail="Scan results not found")

    result = SCAN_RESULTS[scan_id]

    return {
        "scan_id": scan_id,
        "status": "completed",
        "files_scanned": result.files_scanned,
        "scan_duration": result.scan_duration,
        "graph": {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    "description": node.description,
                    "location": {
                        "file_path": node.location.file_path,
                        "line_number": node.location.line_number
                    },
                    "table_name": node.table_name,
                    "endpoint": node.endpoint,
                    "http_method": node.http_method
                }
                for node in result.graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label,
                    "edge_type": edge.edge_type
                }
                for edge in result.graph.edges
            ]
        }
    }


@router.get("/scan/{scan_id}/diagram")
async def get_scan_diagram(
    scan_id: str,
    format: str = Query(default="mermaid", regex="^(mermaid|json|html)$")
):
    """Get workflow diagram in specified format"""
    if scan_id not in SCAN_RESULTS:
        raise HTTPException(status_code=404, detail="Scan results not found")

    result = SCAN_RESULTS[scan_id]

    if format == "json":
        return get_scan_results(scan_id)
    elif format == "mermaid":
        # Generate Mermaid diagram
        nodes = result.graph.nodes
        edges = result.graph.edges

        lines = ["graph TD"]

        # Add nodes with styling
        for node in nodes:
            node_id = node.id.replace("-", "_")
            node_label = f"{node.type.value.upper()}: {node.name}"

            # Color by type
            if "database" in node.type.value:
                color = "fill:#90EE90" if "read" in node.type.value else "fill:#FFA500"
            elif "api" in node.type.value:
                color = "fill:#87CEEB"
            else:
                color = "fill:#FFD700"

            lines.append(f"    {node_id}[\"{node_label}\"]")
            lines.append(f"    style {node_id} {color}")

        # Add edges
        for edge in edges:
            source_id = edge.source.replace("-", "_")
            target_id = edge.target.replace("-", "_")
            label = edge.label or ""
            lines.append(f"    {source_id} --> |{label}| {target_id}")

        return {"diagram": "\n".join(lines), "format": "mermaid"}

    elif format == "html":
        # Return HTML with embedded visualization
        raise HTTPException(status_code=501, detail="HTML format not yet implemented")


async def run_scan(scan_id: str, request: ScanRequest):
    """Background task to run the actual scan"""
    try:
        # Update status to initializing
        SCAN_STATUS[scan_id]["status"] = "initializing"
        SCAN_STATUS[scan_id]["message"] = "Initializing scanner..."
        SCAN_STATUS[scan_id]["progress"] = 0.0

        import re

        # Build configuration
        config = {
            'scanner': {
                'include_extensions': request.file_extensions,
                'exclude_dirs': ['node_modules', 'bin', 'obj', '.git', 'dist', 'build'],
                'detect': {
                    'database': request.detect_database,
                    'api_calls': request.detect_api,
                    'file_io': request.detect_files,
                    'message_queues': request.detect_messages,
                    'data_transforms': request.detect_transforms,
                }
            },
            'output': {
                'directory': f'/tmp/scan-results/{scan_id}',
                'formats': ['json', 'html']
            }
        }

        # Progress callback
        files_discovered = False
        def update_progress(current, total, message):
            nonlocal files_discovered

            if total > 0:
                progress = (current / total) * 100
                SCAN_STATUS[scan_id]["progress"] = progress
                SCAN_STATUS[scan_id]["files_scanned"] = current
                SCAN_STATUS[scan_id]["total_files"] = total

                # Extract ETA from message if present (format: "ETA: 2m 15s")
                eta_match = re.search(r'ETA:\s*([^\|]+)', message)
                if eta_match:
                    SCAN_STATUS[scan_id]["eta"] = eta_match.group(1).strip()

                # Extract nodes count if present (format: "Nodes: 123")
                nodes_match = re.search(r'Nodes:\s*(\d+)', message)
                if nodes_match:
                    SCAN_STATUS[scan_id]["nodes_found"] = int(nodes_match.group(1).replace(',', ''))

                # Update status based on progress
                if current == 0:
                    if not files_discovered:
                        SCAN_STATUS[scan_id]["status"] = "discovering"
                        SCAN_STATUS[scan_id]["message"] = f"Discovering files... Found {total:,} files"
                        files_discovered = True
                    else:
                        SCAN_STATUS[scan_id]["status"] = "scanning"
                        SCAN_STATUS[scan_id]["message"] = "Starting scan..."
                        SCAN_STATUS[scan_id]["eta"] = "Calculating..."
                else:
                    SCAN_STATUS[scan_id]["status"] = "scanning"
                    # Use cleaner message format
                    SCAN_STATUS[scan_id]["message"] = f"Scanning... {current:,}/{total:,} files"
            else:
                SCAN_STATUS[scan_id]["message"] = message

        # Run scan
        builder = WorkflowGraphBuilder(config)

        # Update to discovering status
        SCAN_STATUS[scan_id]["status"] = "discovering"
        SCAN_STATUS[scan_id]["message"] = "Discovering files..."

        result = builder.build(request.repo_path, progress_callback=update_progress)

        # Store results
        SCAN_RESULTS[scan_id] = result

        # Update final status
        SCAN_STATUS[scan_id]["status"] = "completed"
        SCAN_STATUS[scan_id]["progress"] = 100.0
        SCAN_STATUS[scan_id]["message"] = "Scan completed successfully"
        SCAN_STATUS[scan_id]["files_scanned"] = result.files_scanned
        SCAN_STATUS[scan_id]["nodes_found"] = len(result.graph.nodes)
        SCAN_STATUS[scan_id]["eta"] = "0m 0s"
        SCAN_STATUS[scan_id]["total_files"] = result.files_scanned

        # Render outputs
        renderer = WorkflowRenderer(config)
        renderer.render(result)

    except Exception as e:
        SCAN_STATUS[scan_id]["status"] = "failed"
        SCAN_STATUS[scan_id]["message"] = f"Scan failed: {str(e)}"
        SCAN_STATUS[scan_id]["eta"] = None
        print(f"Scan {scan_id} failed: {e}")
        import traceback
        traceback.print_exc()


@router.get("/repositories")
async def list_repositories(
    source: Optional[RepoSourceType] = None,
    organization_id: Optional[str] = None
):
    """
    List available repositories

    - For local mode: List repositories in configured directory
    - For cloud mode: List connected GitHub/GitLab/Bitbucket repos
    """
    if source == RepoSourceType.LOCAL:
        # List local repositories (Docker mount point)
        local_repos_path = os.getenv("LOCAL_REPOS_PATH", "/repos")
        if os.path.exists(local_repos_path):
            repos = [
                {
                    "name": d,
                    "path": os.path.join(local_repos_path, d),
                    "source": "local"
                }
                for d in os.listdir(local_repos_path)
                if os.path.isdir(os.path.join(local_repos_path, d))
            ]
            return {"repositories": repos}
        return {"repositories": []}

    # Cloud repositories (GitHub, GitLab, Bitbucket)
    # TODO: Implement OAuth integration with git providers
    return {
        "repositories": [],
        "message": "Cloud repository integration coming soon"
    }


@router.get("/environment")
async def get_environment():
    """
    Get current environment configuration

    Returns whether running in production (cloud repos only) or local (both cloud and local repos)
    """
    environment = os.getenv("ENVIRONMENT", "development")
    is_docker = os.path.exists("/.dockerenv")

    return {
        "environment": environment,
        "is_docker": is_docker,
        "supports_local_repos": is_docker or environment == "development",
        "supports_cloud_repos": True,
        "local_repos_path": os.getenv("LOCAL_REPOS_PATH", "/repos") if is_docker else None
    }
