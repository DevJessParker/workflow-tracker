"""
WebSocket Router for Real-Time Scan Updates
Provides WebSocket endpoint for clients to receive live scan progress
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.websockets import WebSocketState
import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
import redis.asyncio as aioredis
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'pinata-redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# Track active WebSocket connections per scan
active_connections: Dict[str, Set[WebSocket]] = {}


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
    # Create a fresh Redis client for this WebSocket connection
    redis_client = None
    pubsub = None

    try:
        logger.info(f"[{scan_id}] 🔌 WebSocket connection attempt from {websocket.client}")

        # Accept the WebSocket connection
        await manager.connect(websocket, scan_id)
        logger.info(f"[{scan_id}] ✅ WebSocket accepted")

        # Create async Redis client for this connection
        redis_client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5
        )
        logger.info(f"[{scan_id}] 📡 Redis client created")

        # Test Redis connection
        await redis_client.ping()
        logger.info(f"[{scan_id}] ✅ Redis ping successful")

        # Create pubsub
        pubsub = redis_client.pubsub()
        channel = f"scan:{scan_id}"
        logger.info(f"[{scan_id}] 📡 Pubsub created, subscribing to: {channel}")

        # Subscribe to Redis channel for this scan
        await pubsub.subscribe(channel)
        logger.info(f"[{scan_id}] ✅ Subscribed to Redis channel: {channel}")

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "scan_id": scan_id,
            "message": "WebSocket connection established",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Listen for messages from Redis and forward to WebSocket
        async def listen_redis():
            """Listen for Redis pub/sub messages using async iterator"""
            try:
                # Use async for to listen for messages
                async for message in pubsub.listen():
                    # Skip subscription confirmation messages
                    if message['type'] == 'subscribe':
                        logger.info(f"[{scan_id}] ✅ Subscribed to channel")
                        continue

                    # Process actual messages
                    if message['type'] == 'message':
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

            except Exception as e:
                logger.error(f"[{scan_id}] ❌ Error in Redis listener: {e}")
                raise

        # Listen for client messages (for heartbeat/ping)
        async def listen_client():
            """Listen for client messages (ping/pong for keepalive)"""
            while True:
                try:
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
                    break
                except Exception as e:
                    logger.error(f"[{scan_id}] ❌ Error receiving message: {e}")
                    break

        # Run both listeners concurrently
        await asyncio.gather(
            listen_redis(),
            listen_client(),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        logger.info(f"[{scan_id}] 🔌 WebSocket disconnected normally")

    except Exception as e:
        logger.error(f"[{scan_id}] ❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Internal server error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception as send_error:
            logger.error(f"[{scan_id}] ❌ Error sending error message: {send_error}")

    finally:
        # Clean up
        logger.info(f"[{scan_id}] 🧹 Cleaning up WebSocket connection...")
        manager.disconnect(websocket, scan_id)

        if pubsub:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                logger.info(f"[{scan_id}] ✅ Pubsub closed")
            except Exception as e:
                logger.error(f"[{scan_id}] ❌ Error closing pubsub: {e}")

        if redis_client:
            try:
                await redis_client.close()
                logger.info(f"[{scan_id}] ✅ Redis client closed")
            except Exception as e:
                logger.error(f"[{scan_id}] ❌ Error closing Redis client: {e}")

        logger.info(f"[{scan_id}] ✅ Cleanup complete")


@router.get("/ws/health")
async def websocket_health():
    """
    WebSocket health check endpoint

    Tests Redis connectivity and returns status.
    Frontend should call this before starting scans.
    """
    try:
        # Create test Redis client
        redis_client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2
        )

        # Test connection
        await redis_client.ping()
        await redis_client.close()

        return {
            "status": "healthy",
            "websocket_available": True,
            "redis_connected": True,
            "message": "WebSocket service is ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return {
            "status": "unhealthy",
            "websocket_available": False,
            "redis_connected": False,
            "message": f"WebSocket service unavailable: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


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
