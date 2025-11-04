"""
WebSocket Router for Real-Time Scan Updates
Provides WebSocket endpoint for clients to receive live scan progress
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.websockets import WebSocketState
import asyncio
import json
import logging
import os
from typing import Dict, Set, Optional
from datetime import datetime
import redis.asyncio as aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

# Track active WebSocket connections per scan
active_connections: Dict[str, Set[WebSocket]] = {}

# Async Redis client for WebSocket pub/sub
_redis_client: Optional[aioredis.Redis] = None


async def get_async_redis() -> aioredis.Redis:
    """Get or create async Redis client for WebSocket pub/sub"""
    global _redis_client

    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        _redis_client = await aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5
        )
        logger.info(f"✅ Async Redis client initialized for WebSocket: {redis_url}")

    return _redis_client


class ConnectionManager:
    """Manages WebSocket connections for scan updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, scan_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = set()

        self.active_connections[scan_id].add(websocket)

        logger.info(
            f"[{scan_id}] 🔌 WebSocket connected. "
            f"Total connections for this scan: {len(self.active_connections[scan_id])}"
        )

    def disconnect(self, websocket: WebSocket, scan_id: str):
        """Remove a WebSocket connection"""
        if scan_id in self.active_connections:
            self.active_connections[scan_id].discard(websocket)

            logger.info(
                f"[{scan_id}] 🔌 WebSocket disconnected. "
                f"Remaining connections: {len(self.active_connections[scan_id])}"
            )

            # Clean up empty sets
            if not self.active_connections[scan_id]:
                del self.active_connections[scan_id]

    def get_connection_count(self, scan_id: str) -> int:
        """Get number of active connections for a scan"""
        return len(self.active_connections.get(scan_id, set()))

    async def send_message(self, websocket: WebSocket, message: dict):
        """Send message to a specific WebSocket"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
                return True
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
        return False


manager = ConnectionManager()


@router.websocket("/ws/scan/{scan_id}")
async def scan_websocket(websocket: WebSocket, scan_id: str):
    """
    WebSocket endpoint for real-time scan updates

    Clients connect to this endpoint to receive live progress updates
    for a specific scan. Updates are published via Redis pub/sub.

    Args:
        websocket: WebSocket connection
        scan_id: Unique identifier for the scan to monitor
    """
    logger.info(f"[{scan_id}] 🔌 New WebSocket connection request")

    try:
        await manager.connect(websocket, scan_id)
        logger.info(f"[{scan_id}] ✅ WebSocket accepted and connected")
    except Exception as e:
        logger.error(f"[{scan_id}] ❌ Failed to accept WebSocket: {e}")
        raise

    # Get async Redis client
    redis = await get_async_redis()
    pubsub = redis.pubsub()
    channel = f"scan:{scan_id}"

    try:
        # Subscribe to Redis channel for this scan
        await pubsub.subscribe(channel)
        logger.info(f"[{scan_id}] 📡 Subscribed to Redis channel: {channel}")

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "scan_id": scan_id,
            "message": "WebSocket connection established",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Listen for messages from Redis and forward to WebSocket
        async def listen_redis():
            """Listen for Redis pub/sub messages"""
            try:
                async for message in pubsub.listen():
                    if message and message['type'] == 'message':
                        try:
                            # Parse the message data
                            data = json.loads(message['data'])

                            # Add metadata
                            data['type'] = 'scan_update'
                            data['timestamp'] = datetime.utcnow().isoformat()

                            # Send to WebSocket client
                            success = await manager.send_message(websocket, data)

                            if success:
                                logger.debug(
                                    f"[{scan_id}] 📤 Sent update: "
                                    f"{data.get('status')} - {data.get('progress', 0):.1f}%"
                                )
                        except json.JSONDecodeError as e:
                            logger.error(f"[{scan_id}] ❌ Invalid JSON from Redis: {e}")
                        except Exception as e:
                            logger.error(f"[{scan_id}] ❌ Error processing message: {e}")
            except asyncio.CancelledError:
                logger.info(f"[{scan_id}] 🛑 Redis listener cancelled")
                raise
            except Exception as e:
                logger.error(f"[{scan_id}] ❌ Error in Redis listener: {e}")

        # Listen for client messages (for heartbeat/ping)
        async def listen_client():
            """Listen for client messages (ping/pong for keepalive)"""
            try:
                while True:
                    message = await websocket.receive_text()

                    # Handle ping/pong for keepalive
                    if message == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        logger.debug(f"[{scan_id}] 🏓 Ping/pong")

            except WebSocketDisconnect:
                logger.info(f"[{scan_id}] 🔌 Client disconnected")
                raise
            except asyncio.CancelledError:
                logger.info(f"[{scan_id}] 🛑 Client listener cancelled")
                raise
            except Exception as e:
                logger.error(f"[{scan_id}] ❌ Error receiving message: {e}")
                raise

        # Run both listeners concurrently
        tasks = [
            asyncio.create_task(listen_redis()),
            asyncio.create_task(listen_client())
        ]

        # Wait for either task to complete/fail
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Retrieve exceptions from completed tasks to avoid "exception was never retrieved" warnings
        for task in done:
            try:
                task.result()  # This will re-raise any exception
            except (WebSocketDisconnect, asyncio.CancelledError):
                # Expected exceptions - client disconnected or task was cancelled
                pass
            except Exception as e:
                logger.error(f"[{scan_id}] ❌ Task error: {e}")

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        logger.info(f"[{scan_id}] 🔌 WebSocket disconnected normally")

    except Exception as e:
        logger.error(f"[{scan_id}] ❌ WebSocket error: {e}")
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except:
            pass

    finally:
        # Clean up
        manager.disconnect(websocket, scan_id)
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception as e:
            logger.error(f"[{scan_id}] ⚠️  Error closing pubsub: {e}")

        logger.info(f"[{scan_id}] 🧹 Cleaned up WebSocket connection")


@router.get("/ws/scan/{scan_id}/connections")
async def get_connection_count(scan_id: str):
    """
    Get the number of active WebSocket connections for a scan

    Useful for debugging and monitoring
    """
    count = manager.get_connection_count(scan_id)
    return {
        "scan_id": scan_id,
        "active_connections": count,
        "timestamp": datetime.utcnow().isoformat()
    }
