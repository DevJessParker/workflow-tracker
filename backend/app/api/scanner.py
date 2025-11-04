"""
Scanner API Routes - Handles code scanning operations
"""
import asyncio
import json
import os
import sys
import uuid
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

router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])

# Redis connection
redis_client: Optional[aioredis.Redis] = None


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
            redis, scan_id, "discovering", 0.0, "Discovering files...", 0, 0
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

        # Create progress callback
        total_files_estimate = 0

        def progress_callback(current, total, message):
            nonlocal total_files_estimate
            total_files_estimate = total
            progress_pct = (current / total) * 100 if total > 0 else 0

            # Run async publish in the event loop
            asyncio.create_task(publish_progress(
                redis, scan_id, "scanning", progress_pct,
                message, current, current * 3  # Rough estimate of nodes
            ))

        # Run scanner in thread pool to avoid blocking
        def run_scanner():
            builder = WorkflowGraphBuilder(scanner_config)
            return builder.build(request.repo_path, progress_callback=progress_callback)

        # Execute in thread pool
        loop = asyncio.get_event_loop()
        result: ScannerScanResult = await loop.run_in_executor(None, run_scanner)

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
                    'method': node.method,
                }
                for node in result.graph.nodes
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'label': edge.label,
                    'metadata': edge.metadata,
                }
                for edge in result.graph.edges
            ],
            'scan_time_seconds': result.scan_time_seconds,
            'errors': result.errors,
        }

        with open(output_dir / 'results.json', 'w') as f:
            json.dump(result_json, f, indent=2)

        # Complete scan
        await publish_progress(
            redis, scan_id, "completed", 100.0,
            f"Scan completed successfully", result.files_scanned, len(result.graph.nodes)
        )

        print(f"[{scan_id}] ✅ Scan completed: {result.files_scanned} files, {len(result.graph.nodes)} nodes")

    except Exception as e:
        print(f"[{scan_id}] ❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        await publish_progress(
            redis, scan_id, "error", 0.0, f"Scan failed: {str(e)}", 0, 0
        )


async def publish_progress(
    redis: aioredis.Redis,
    scan_id: str,
    status: str,
    progress: float,
    message: str,
    files_scanned: int,
    nodes_found: int,
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
        "total_files": None,
    }

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


def _generate_mermaid_diagram(results: dict) -> str:
    """Generate Mermaid flowchart from scan results"""
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
