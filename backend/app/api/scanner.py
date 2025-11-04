"""
Scanner API Routes - Handles code scanning operations
"""
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel, ValidationError

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

        # Simulate file discovery and scanning
        # In reality, you would call your scanner here
        await asyncio.sleep(1)

        # Simulate progress updates
        total_files = 100  # This would come from your scanner
        for i in range(1, total_files + 1):
            progress = (i / total_files) * 100
            await publish_progress(
                redis, scan_id, "scanning", progress,
                f"Scanning file {i}/{total_files}", i, i * 3
            )
            await asyncio.sleep(0.1)  # Simulate scanning time

        # Complete scan
        await publish_progress(
            redis, scan_id, "completed", 100.0,
            "Scan completed successfully", total_files, total_files * 3
        )

        print(f"[{scan_id}] ✅ Scan completed: {total_files} files, {total_files * 3} nodes")

    except Exception as e:
        print(f"[{scan_id}] ❌ Scan failed: {e}")
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
