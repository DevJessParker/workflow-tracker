"""
Redis Client for Pub/Sub
Handles real-time communication between scan workers and WebSocket clients
"""

import redis
import redis.asyncio as aioredis
import json
import os
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

# Redis connection configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'pinata-redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# Create synchronous Redis client (for non-async contexts)
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,  # Automatically decode responses to strings
    socket_connect_timeout=5,
    socket_keepalive=True,
    health_check_interval=30
)

# Create async Redis client (for async contexts like WebSockets)
async_redis_client = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
    health_check_interval=30
)


def publish_scan_update(scan_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Publish scan progress update to Redis channel (synchronous)

    Args:
        scan_id: Unique scan identifier
        update_data: Dictionary containing scan status, progress, etc.

    Returns:
        True if published successfully, False otherwise
    """
    try:
        channel = f"scan:{scan_id}"
        message = json.dumps(update_data)

        # Publish to Redis channel
        subscribers = redis_client.publish(channel, message)

        logger.debug(f"[{scan_id}] 📡 Published update to {subscribers} subscriber(s): {update_data.get('progress', 0):.1f}%")

        return True

    except redis.RedisError as e:
        logger.error(f"[{scan_id}] ❌ Redis publish error: {e}")
        return False
    except Exception as e:
        logger.error(f"[{scan_id}] ❌ Unexpected error publishing to Redis: {e}")
        return False


async def async_publish_scan_update(scan_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Publish scan progress update to Redis channel (async)

    Args:
        scan_id: Unique scan identifier
        update_data: Dictionary containing scan status, progress, etc.

    Returns:
        True if published successfully, False otherwise
    """
    try:
        channel = f"scan:{scan_id}"
        message = json.dumps(update_data)

        # Publish to Redis channel
        subscribers = await async_redis_client.publish(channel, message)

        logger.debug(f"[{scan_id}] 📡 Published update to {subscribers} subscriber(s): {update_data.get('progress', 0):.1f}%")

        return True

    except aioredis.RedisError as e:
        logger.error(f"[{scan_id}] ❌ Redis publish error: {e}")
        return False
    except Exception as e:
        logger.error(f"[{scan_id}] ❌ Unexpected error publishing to Redis: {e}")
        return False


def check_redis_connection() -> bool:
    """
    Check if Redis connection is healthy

    Returns:
        True if connected, False otherwise
    """
    try:
        redis_client.ping()
        logger.info("✅ Redis connection healthy")
        return True
    except redis.ConnectionError as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected Redis error: {e}")
        return False


def get_redis_info() -> Dict[str, Any]:
    """
    Get Redis server information for debugging

    Returns:
        Dictionary with Redis server info
    """
    try:
        info = redis_client.info()
        return {
            "connected": True,
            "version": info.get('redis_version'),
            "uptime_seconds": info.get('uptime_in_seconds'),
            "connected_clients": info.get('connected_clients'),
            "used_memory_human": info.get('used_memory_human')
        }
    except Exception as e:
        logger.error(f"❌ Failed to get Redis info: {e}")
        return {"connected": False, "error": str(e)}


# Test connection on import
if __name__ != "__main__":
    if check_redis_connection():
        info = get_redis_info()
        logger.info(f"📊 Redis: {info.get('connected_clients', 0)} clients, {info.get('used_memory_human', 'unknown')} memory")
