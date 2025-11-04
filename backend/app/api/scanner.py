"""
Scanner API Routes - Handles code scanning operations
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel, ValidationError

# Add scanner directory to Python path
SCANNER_DIR = Path(__file__).parent.parent.parent.parent / "scanner"
sys.path.insert(0, str(SCANNER_DIR))

# Import scanner components
from graph.builder import WorkflowGraphBuilder
from models import ScanResult as ScannerScanResult
from workflow_analyzer import WorkflowAnalyzer
from database_analyzer import DatabaseTableAnalyzer
from api_analyzer import APIRoutesAnalyzer
from component_analyzer import ComponentPageAnalyzer
from dependency_analyzer import DependencyAnalyzer

# Import backend services
from app.models.scan import ScanMetadata, ScanListResponse, UnviewedCountResponse
from app.services.scan_storage import ScanStorage

router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])

# Redis connection
redis_client: Optional[aioredis.Redis] = None

# Scan storage service
scan_storage = ScanStorage()


async def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        redis_client = await aioredis.from_url(redis_url, decode_responses=True)
    return redis_client


class ScanRequest(BaseModel):
    """Scan request model - matches frontend format"""
    repo_path: str
    source_type: str = "local"
    file_extensions: List[str] = [".cs", ".ts", ".html", ".xaml"]
    detect_database: bool = True
    detect_api: bool = True
    detect_files: bool = True
    detect_messages: bool = True
    detect_transforms: bool = True


class ScanResponse(BaseModel):
    """Scan response model"""
    scan_id: str
    status: str
    message: str


@router.get("/environment")
async def get_environment():
    """Get scanner environment info"""
    return {
        "status": "ready",
        "scanner_version": "1.0.0",
        "supported_languages": ["C#", "TypeScript", "HTML", "XAML"],
        "is_docker": os.getenv("IS_DOCKER", "false").lower() == "true",
        "supports_local_repos": True,  # Enable Local/Cloud toggle
        "supports_github": False,
        "supports_gitlab": False,
        "supports_bitbucket": False,
    }


@router.get("/repositories")
async def get_repositories(source: str = "local"):
    """Get available repositories"""
    repos_dir = Path("/repos")
    if not repos_dir.exists():
        return []

    repositories = []
    for repo_path in repos_dir.iterdir():
        if repo_path.is_dir() and not repo_path.name.startswith("."):
            repositories.append({
                "name": repo_path.name,
                "path": str(repo_path),
                "source": source,
            })

    return repositories


@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest, raw_request: Request = None):
    """Start a code scan"""
    scan_id = str(uuid.uuid4())

    # Log scan start with request details
    print(f"[{scan_id}] ✅ Scan queued, starting background task...")
    print(f"[{scan_id}] 📁 Repository: {request.repo_path}")
    print(f"[{scan_id}] 📝 File extensions: {request.file_extensions}")
    print(f"[{scan_id}] 🔍 Detections: DB={request.detect_database}, API={request.detect_api}, Files={request.detect_files}")

    # Create scan metadata entry
    scan_metadata = ScanMetadata(
        scan_id=scan_id,
        repository_path=request.repo_path,
        scan_type="full",  # Default to full scan
        performed_by="system",  # TODO: Get from auth context
        created_at=datetime.utcnow().isoformat(),
        status="queued",
        viewed=False,
    )
    scan_storage.create_scan(scan_metadata)
    print(f"[{scan_id}] 💾 Scan metadata created")

    # Initialize scan status in Redis
    redis = await get_redis()
    scan_status = {
        "scan_id": scan_id,
        "status": "queued",
        "progress": 0.0,
        "message": "Scan queued",
        "files_scanned": 0,
        "nodes_found": 0,
        "eta": None,
        "total_files": None,
    }

    await redis.set(
        f"scan:status:{scan_id}",
        json.dumps(scan_status),
        ex=3600  # Expire after 1 hour
    )

    # Start scan in background
    asyncio.create_task(run_scan(scan_id, request))

    print(f"[{scan_id}] 📤 Returning response immediately to frontend")

    return ScanResponse(
        scan_id=scan_id,
        status="queued",
        message="Scan started successfully"
    )


async def run_scan(scan_id: str, request: ScanRequest):
    """Run the actual scan in background"""
    redis = await get_redis()

    try:
        # Update status to discovering
        await publish_progress(
            redis, scan_id, "discovering", 0.0, "Discovering files...", 0, 0, 0
        )

        # Create scanner configuration
        scanner_config = {
            'scanner': {
                'include_extensions': request.file_extensions,
                'exclude_dirs': [
                    'node_modules', 'bin', 'obj', '.git', '.vs', 'dist',
                    'build', 'coverage', '.next', '__pycache__', 'venv'
                ],
                'exclude_patterns': ['*.min.js', '*.bundle.js', '*.generated.cs'],
                'detect': {
                    'database': request.detect_database,
                    'api_calls': request.detect_api,
                    'file_operations': request.detect_files,
                    'message_queues': request.detect_messages,
                    'data_transforms': request.detect_transforms,
                },
                'edge_inference': {
                    'enabled': True,
                    'proximity_edges': True,
                    'data_flow_edges': True,
                    'max_line_distance': 20,
                }
            },
            'output': {
                'directory': f'/tmp/scans/{scan_id}',
                'formats': ['json', 'html'],
            }
        }

        # Get the current event loop to schedule callbacks from thread
        loop = asyncio.get_event_loop()

        # Create progress callback that schedules coroutines from thread
        total_files_estimate = 0

        def progress_callback(current, total, message):
            nonlocal total_files_estimate
            total_files_estimate = total
            progress_pct = (current / total) * 100 if total > 0 else 0

            # Schedule coroutine from thread to main event loop
            asyncio.run_coroutine_threadsafe(
                publish_progress(
                    redis, scan_id, "scanning", progress_pct,
                    message, current, current * 3,  # Rough estimate of nodes
                    total  # Total files discovered
                ),
                loop
            )

        # Run scanner in thread pool to avoid blocking
        def run_scanner():
            builder = WorkflowGraphBuilder(scanner_config)
            return builder.build(request.repo_path, progress_callback=progress_callback)

        # Execute in thread pool
        result: ScannerScanResult = await loop.run_in_executor(None, run_scanner)

        # Initialize analysis steps
        analysis_steps = [
            {"name": "Inferring Workflow Edges", "status": "completed", "progress": 100, "icon": "🔗"},
            {"name": "Analyzing UI Workflows", "status": "pending", "progress": 0, "icon": "🔍"},
            {"name": "Analyzing Database Tables", "status": "pending", "progress": 0, "icon": "💾"},
            {"name": "Analyzing API Routes", "status": "pending", "progress": 0, "icon": "🌐"},
            {"name": "Analyzing Components & Pages", "status": "pending", "progress": 0, "icon": "🧩"},
            {"name": "Analyzing Dependencies", "status": "pending", "progress": 0, "icon": "📦"},
        ]

        # Send initial analysis state
        print(f"[{scan_id}] 📊 Starting analysis phase with {len(analysis_steps)} steps...")
        await publish_progress(
            redis, scan_id, "analyzing", 100.0, "Starting analysis...",
            result.files_scanned, len(result.graph.nodes), total_files_estimate, analysis_steps
        )

        # Helper function to update analysis step progress
        async def update_analysis_step(step_index: int, status: str, progress: int):
            analysis_steps[step_index]["status"] = status
            analysis_steps[step_index]["progress"] = progress
            overall_progress = sum(step["progress"] for step in analysis_steps) / len(analysis_steps)
            await publish_progress(
                redis, scan_id, "analyzing", 100.0, f"{analysis_steps[step_index]['icon']} {analysis_steps[step_index]['name']}...",
                result.files_scanned, len(result.graph.nodes), total_files_estimate, analysis_steps
            )

        # Analyze UI workflows
        print(f"[{scan_id}] 🔍 Analyzing UI workflows...")
        await update_analysis_step(1, "in_progress", 0)
        analyzer = WorkflowAnalyzer(result.graph)
        workflows = analyzer.analyze()
        await update_analysis_step(1, "completed", 100)

        # Analyze database tables
        print(f"[{scan_id}] 💾 Analyzing database tables...")
        await update_analysis_step(2, "in_progress", 0)
        db_analyzer = DatabaseTableAnalyzer(result.graph, request.repo_path)
        database_tables = db_analyzer.analyze()
        database_tables_dict = db_analyzer.to_dict()
        await update_analysis_step(2, "completed", 100)

        # Analyze API routes
        print(f"[{scan_id}] 🌐 Analyzing API routes...")
        await update_analysis_step(3, "in_progress", 0)
        api_analyzer = APIRoutesAnalyzer(result.graph, request.repo_path)
        api_routes = api_analyzer.analyze()
        api_routes_dict = api_analyzer.to_dict()
        await update_analysis_step(3, "completed", 100)

        # Analyze components and pages
        print(f"[{scan_id}] 🧩 Analyzing components and pages...")
        await update_analysis_step(4, "in_progress", 0)
        component_analyzer = ComponentPageAnalyzer(result.graph, request.repo_path)
        components, pages = component_analyzer.analyze()
        components_pages_dict = component_analyzer.to_dict()
        await update_analysis_step(4, "completed", 100)

        # Analyze dependencies
        print(f"[{scan_id}] 📦 Analyzing dependencies...")
        await update_analysis_step(5, "in_progress", 0)
        dependency_analyzer = DependencyAnalyzer(request.repo_path)
        dependencies = dependency_analyzer.analyze()
        dependencies_dict = dependency_analyzer.to_dict()
        await update_analysis_step(5, "completed", 100)

        # Save results to disk
        output_dir = Path(f'/tmp/scans/{scan_id}')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON result
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
                    'http_method': node.method,  # Changed from 'method' to match frontend
                }
                for node in result.graph.nodes
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'label': edge.label,
                    'edge_type': edge.label,  # Added for frontend compatibility
                    'metadata': edge.metadata,
                }
                for edge in result.graph.edges
            ],
            'workflows': [
                {
                    'id': wf.id,
                    'name': wf.name,
                    'summary': wf.summary,
                    'outcome': wf.outcome,
                    'trigger': {
                        'name': wf.trigger.name,
                        'description': wf.trigger.description,
                        'interaction_type': wf.trigger.interaction_type,
                        'component': wf.trigger.component,
                        'location': wf.trigger.location,
                    },
                    'steps': [
                        {
                            'step_number': step.step_number,
                            'title': step.title,
                            'description': step.description,
                            'technical_details': step.technical_details,
                            'icon': step.icon,
                            'node_id': step.node.id,
                        }
                        for step in wf.steps
                    ],
                    'story': wf.to_story(),
                }
                for wf in workflows
            ],
            'database_tables': database_tables_dict,
            'api_routes': api_routes_dict,
            'components': components_pages_dict['components'],
            'pages': components_pages_dict['pages'],
            'dependencies': dependencies_dict['dependencies'],
            'dependency_conflicts': dependencies_dict['conflicts'],
            'dependency_metrics': dependencies_dict['metrics'],
            'scan_time_seconds': result.scan_time_seconds,
            'scan_duration': result.scan_time_seconds,  # Alias for frontend compatibility
            'errors': result.errors,
        }

        with open(output_dir / 'results.json', 'w') as f:
            json.dump(result_json, f, indent=2)

        print(f"[{scan_id}] ✅ Found {len(workflows)} UI workflows")
        print(f"[{scan_id}] ✅ Analyzed {len(database_tables_dict)} database tables")
        print(f"[{scan_id}] ✅ Analyzed {len(api_routes_dict)} API routes")
        print(f"[{scan_id}] ✅ Analyzed {len(components_pages_dict['components'])} components")
        print(f"[{scan_id}] ✅ Analyzed {len(components_pages_dict['pages'])} pages")
        print(f"[{scan_id}] ✅ Analyzed {len(dependencies_dict['dependencies'])} dependencies")
        print(f"[{scan_id}] ⚠️  Found {len(dependencies_dict['conflicts'])} conflicts, {dependencies_dict['metrics']['unused_count']} unused")

        # Complete scan
        await publish_progress(
            redis, scan_id, "completed", 100.0,
            f"Scan completed successfully", result.files_scanned, len(result.graph.nodes),
            total_files_estimate
        )

        # Update scan metadata
        scan_storage.update_scan(scan_id, {
            'status': 'completed',
            'completed_at': datetime.utcnow().isoformat(),
            'files_scanned': result.files_scanned,
            'nodes_found': len(result.graph.nodes),
            'total_files': total_files_estimate,
            'scan_duration': result.scan_time_seconds,
            'errors': result.errors,
        })
        print(f"[{scan_id}] 💾 Scan metadata updated")

        print(f"[{scan_id}] ✅ Scan completed: {result.files_scanned} files, {len(result.graph.nodes)} nodes")

    except Exception as e:
        print(f"[{scan_id}] ❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        await publish_progress(
            redis, scan_id, "error", 0.0, f"Scan failed: {str(e)}", 0, 0, 0
        )

        # Update scan metadata with error
        scan_storage.update_scan(scan_id, {
            'status': 'error',
            'completed_at': datetime.utcnow().isoformat(),
            'errors': [str(e)],
        })
        print(f"[{scan_id}] 💾 Scan metadata updated with error")


async def publish_progress(
    redis: aioredis.Redis,
    scan_id: str,
    status: str,
    progress: float,
    message: str,
    files_scanned: int,
    nodes_found: int,
    total_files: int = None,
    analysis_steps: List[Dict] = None,
):
    """Publish scan progress to Redis"""
    scan_status = {
        "scan_id": scan_id,
        "status": status,
        "progress": progress,
        "message": message,
        "files_scanned": files_scanned,
        "nodes_found": nodes_found,
        "eta": None,
        "total_files": total_files,
    }

    # Add analysis steps if provided
    if analysis_steps is not None:
        scan_status["analysis_steps"] = analysis_steps

    # Store in Redis
    await redis.set(
        f"scan:status:{scan_id}",
        json.dumps(scan_status),
        ex=3600
    )

    # Publish to channel for WebSocket subscribers
    await redis.publish(
        f"scan:progress:{scan_id}",
        json.dumps(scan_status)
    )

    print(f"[{scan_id}] 📊 Status set to '{status}' - frontend can now see this")


@router.websocket("/ws/scan/{scan_id}")
async def websocket_scan_progress(websocket: WebSocket, scan_id: str):
    """WebSocket endpoint for real-time scan progress updates"""
    await websocket.accept()
    print(f"[{scan_id}] 🔌 WebSocket connected")

    redis = await get_redis()

    try:
        # Send connection confirmation
        connected_msg = {
            "type": "connected",
            "scan_id": scan_id,
            "message": "Connected to scan progress stream"
        }
        await websocket.send_text(json.dumps(connected_msg))
        print(f"[{scan_id}] 📤 Sent connection confirmation")

        # Send current status immediately if available
        current_status = await redis.get(f"scan:status:{scan_id}")
        if current_status:
            status_data = json.loads(current_status)
            update_msg = {
                "type": "scan_update",
                "scan_id": status_data.get("scan_id"),
                "status": status_data.get("status"),
                "progress": status_data.get("progress"),
                "message": status_data.get("message"),
                "files_scanned": status_data.get("files_scanned"),
                "total_files": status_data.get("total_files"),
                "nodes_found": status_data.get("nodes_found"),
                "eta": status_data.get("eta"),
                "timestamp": "now"
            }
            await websocket.send_text(json.dumps(update_msg))
            print(f"[{scan_id}] 📤 Sent current status: {status_data.get('status')}")

        # Subscribe to progress updates
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"scan:progress:{scan_id}")

        print(f"[{scan_id}] 📡 Subscribed to Redis channel")

        # Listen for updates
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])

                # Wrap the progress data with type field
                update_msg = {
                    "type": "scan_update",
                    "scan_id": data.get("scan_id"),
                    "status": data.get("status"),
                    "progress": data.get("progress"),
                    "message": data.get("message"),
                    "files_scanned": data.get("files_scanned"),
                    "total_files": data.get("total_files"),
                    "nodes_found": data.get("nodes_found"),
                    "eta": data.get("eta"),
                    "timestamp": "now"
                }

                await websocket.send_text(json.dumps(update_msg))
                print(f"[{scan_id}] 📤 Sent progress update: {data.get('status')} - {data.get('progress')}%")

                # Check if scan is complete
                if data["status"] in ["completed", "error", "failed"]:
                    print(f"[{scan_id}] ✅ Scan finished, closing WebSocket")
                    break

        await pubsub.unsubscribe(f"scan:progress:{scan_id}")
        await pubsub.close()

    except WebSocketDisconnect:
        print(f"[{scan_id}] 🔌 WebSocket disconnected by client")
    except Exception as e:
        print(f"[{scan_id}] ❌ WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        print(f"[{scan_id}] 🔌 WebSocket closed")


@router.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get scan results for a completed scan"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    return results


@router.get("/scan/{scan_id}/diagram")
async def get_scan_diagram(scan_id: str, format: str = "mermaid"):
    """Generate workflow diagram for scan results

    Args:
        scan_id: Scan ID
        format: Diagram format (mermaid, dot, json)
    """
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    if format == "mermaid":
        # Generate Mermaid diagram
        diagram = _generate_mermaid_diagram(results)
        return {"format": "mermaid", "diagram": diagram}
    elif format == "json":
        # Return raw graph data
        return {
            "format": "json",
            "nodes": results['nodes'],
            "edges": results['edges']
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@router.get("/scan/{scan_id}/workflows")
async def get_ui_workflows(scan_id: str):
    """Get user-friendly UI workflows from scan results"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    workflows = results.get('workflows', [])

    return {
        'scan_id': scan_id,
        'total_workflows': len(workflows),
        'workflows': workflows
    }


@router.get("/scan/{scan_id}/workflows/{workflow_id}/diagram")
async def get_workflow_diagram(scan_id: str, workflow_id: str):
    """Get user-friendly diagram for a specific workflow"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    workflows = results.get('workflows', [])
    workflow = next((w for w in workflows if w['id'] == workflow_id), None)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Generate user-friendly Mermaid diagram
    diagram = _generate_workflow_diagram(workflow)

    return {
        'workflow_id': workflow_id,
        'name': workflow['name'],
        'diagram': diagram,
        'story': workflow['story']
    }


def _generate_mermaid_diagram(results: dict) -> str:
    """Generate Mermaid flowchart from scan results (technical view)"""
    lines = ["graph TD"]

    # Add nodes
    for node in results['nodes']:
        node_id = node['id'].replace('-', '_')
        node_label = f"{node['name']}<br/>{node['type']}"

        # Style based on type
        if 'database' in node['type']:
            shape = f'{node_id}[("{node_label}")]'
        elif 'api' in node['type']:
            shape = f'{node_id}(["{node_label}"])'
        else:
            shape = f'{node_id}["{node_label}"]'

        lines.append(f"    {shape}")

    # Add edges
    for edge in results['edges']:
        source = edge['source'].replace('-', '_')
        target = edge['target'].replace('-', '_')
        label = edge.get('label', '')

        if label:
            lines.append(f"    {source} -->|{label}| {target}")
        else:
            lines.append(f"    {source} --> {target}")

    return '\n'.join(lines)


def _generate_workflow_diagram(workflow: dict) -> str:
    """Generate user-friendly Mermaid diagram for a workflow"""
    lines = [
        "graph TD",
        "    classDef userAction fill:#4CAF50,stroke:#45a049,stroke-width:3px,color:#fff",
        "    classDef database fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#fff",
        "    classDef api fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#fff",
        "    classDef process fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#fff",
        "    classDef result fill:#4CAF50,stroke:#45a049,stroke-width:2px,color:#fff",
        ""
    ]

    # Add trigger node
    trigger = workflow['trigger']
    trigger_id = "start"
    lines.append(f'    {trigger_id}["{trigger["description"]}"]:::userAction')

    # Add workflow steps
    prev_id = trigger_id
    for step in workflow['steps']:
        step_id = f"step{step['step_number']}"
        label = f"{step['icon']} {step['title']}"

        # Determine class based on description
        if 'database' in step['title'].lower() or 'save' in step['title'].lower():
            node_class = "database"
        elif 'api' in step['title'].lower() or 'call' in step['title'].lower():
            node_class = "api"
        else:
            node_class = "process"

        lines.append(f'    {step_id}["{label}"]:::{node_class}')
        lines.append(f'    {prev_id} --> {step_id}')
        prev_id = step_id

    # Add result node
    result_id = "result"
    outcome = workflow['outcome']
    lines.append(f'    {result_id}["{outcome}"]:::result')
    lines.append(f'    {prev_id} --> {result_id}')

    return "\n".join(lines)


# ============================================================================
# Scan History Endpoints
# ============================================================================

@router.get("/scans", response_model=ScanListResponse)
async def list_scans(limit: Optional[int] = 100, offset: int = 0):
    """List all scans with pagination"""
    scans = scan_storage.list_scans(limit=limit, offset=offset)
    total = scan_storage.count_total_scans()

    return ScanListResponse(
        total=total,
        scans=scans
    )


@router.get("/scans/unviewed/count", response_model=UnviewedCountResponse)
async def get_unviewed_count():
    """Get count of unviewed scans"""
    count = scan_storage.count_unviewed_scans()
    return UnviewedCountResponse(count=count)


@router.patch("/scans/{scan_id}/viewed")
async def mark_scan_as_viewed(scan_id: str):
    """Mark a scan as viewed"""
    success = scan_storage.mark_as_viewed(scan_id)

    if not success:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {"success": True, "scan_id": scan_id, "viewed": True}


@router.get("/scan/{scan_id}/database-tables")
async def get_database_tables(scan_id: str):
    """Get database table analysis for a scan"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    database_tables = results.get('database_tables', {})

    return {
        'scan_id': scan_id,
        'tables': database_tables,
        'table_count': len(database_tables)
    }


@router.get("/scan/{scan_id}/api-routes")
async def get_api_routes(scan_id: str):
    """Get API routes analysis for a scan"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    api_routes = results.get('api_routes', {})

    return {
        'scan_id': scan_id,
        'routes': api_routes,
        'route_count': len(api_routes)
    }


@router.get("/scan/{scan_id}/components")
async def get_components(scan_id: str):
    """Get components analysis for a scan"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    components = results.get('components', {})

    return {
        'scan_id': scan_id,
        'components': components,
        'component_count': len(components)
    }


@router.get("/scan/{scan_id}/pages")
async def get_pages(scan_id: str):
    """Get pages analysis for a scan"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    pages = results.get('pages', {})

    return {
        'scan_id': scan_id,
        'pages': pages,
        'page_count': len(pages)
    }


@router.get("/scan/{scan_id}/dependencies")
async def get_dependencies(scan_id: str):
    """Get dependencies analysis for a scan"""
    results_file = Path(f'/tmp/scans/{scan_id}/results.json')

    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")

    with open(results_file, 'r') as f:
        results = json.load(f)

    dependencies = results.get('dependencies', {})
    conflicts = results.get('dependency_conflicts', [])
    metrics = results.get('dependency_metrics', {})

    return {
        'scan_id': scan_id,
        'dependencies': dependencies,
        'conflicts': conflicts,
        'metrics': metrics,
        'dependency_count': len(dependencies)
    }
