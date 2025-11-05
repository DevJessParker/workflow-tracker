#!/usr/bin/env python3
"""
Complete WebSocket Flow Test
Tests the entire flow: Publisher -> Redis -> WebSocket Subscriber

This script simulates:
1. Publishing scan updates to Redis (like the scanner does)
2. Connecting to the WebSocket endpoint (like the frontend does)
3. Verifying messages flow through correctly
"""

import asyncio
import json
import os
import sys
from typing import Optional

# Test configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
WS_URL = os.getenv('WS_URL', 'ws://localhost:8000/ws/scan/')
TEST_SCAN_ID = 'test-websocket-flow-123'


async def test_complete_flow():
    """Test the complete publisher -> Redis -> WebSocket flow"""
    print("=" * 60)
    print("🧪 Testing Complete WebSocket Flow")
    print("=" * 60)
    print()

    # Import required modules
    try:
        import redis.asyncio as aioredis
        import websockets
    except ImportError as e:
        print(f"❌ Missing required module: {e}")
        print("💡 Install with: pip install redis websockets")
        return False

    # Step 1: Test Redis connection
    print("📡 Step 1: Testing Redis connection...")
    try:
        redis_client = await aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5
        )
        await redis_client.ping()
        print("✅ Redis connection OK")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

    # Step 2: Connect to WebSocket
    print()
    print("🔌 Step 2: Connecting to WebSocket...")
    ws_url = f"{WS_URL}{TEST_SCAN_ID}"
    print(f"   URL: {ws_url}")

    try:
        websocket = await websockets.connect(ws_url)
        print("✅ WebSocket connected successfully")
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print()
        print("💡 Troubleshooting tips:")
        print("   1. Make sure the backend is running: docker-compose ps")
        print("   2. Check backend logs: docker-compose logs backend")
        print("   3. Verify the backend is accessible: curl http://localhost:8000/health")
        await redis_client.close()
        return False

    # Step 3: Wait for connection confirmation
    print()
    print("📨 Step 3: Waiting for connection confirmation...")
    try:
        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(message)

        if data.get('type') == 'connected':
            print(f"✅ Received connection confirmation: {data.get('message')}")
        else:
            print(f"⚠️  Unexpected message type: {data}")
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for connection confirmation")
        await websocket.close()
        await redis_client.close()
        return False
    except Exception as e:
        print(f"❌ Error receiving message: {e}")
        await websocket.close()
        await redis_client.close()
        return False

    # Step 4: Publish test messages and verify they're received
    print()
    print("📤 Step 4: Publishing test messages to Redis...")

    test_messages = [
        {
            "scan_id": TEST_SCAN_ID,
            "status": "discovering",
            "progress": 0.0,
            "message": "Discovering files...",
            "files_scanned": 0,
            "nodes_found": 0,
        },
        {
            "scan_id": TEST_SCAN_ID,
            "status": "scanning",
            "progress": 25.0,
            "message": "Scanning files... 250/1000",
            "files_scanned": 250,
            "nodes_found": 45,
            "eta": "2m 15s",
            "total_files": 1000
        },
        {
            "scan_id": TEST_SCAN_ID,
            "status": "scanning",
            "progress": 50.0,
            "message": "Scanning files... 500/1000",
            "files_scanned": 500,
            "nodes_found": 92,
            "eta": "1m 30s",
            "total_files": 1000
        },
        {
            "scan_id": TEST_SCAN_ID,
            "status": "completed",
            "progress": 100.0,
            "message": "Scan completed successfully",
            "files_scanned": 1000,
            "nodes_found": 187,
            "eta": "0m 0s",
            "total_files": 1000
        }
    ]

    received_count = 0
    expected_count = len(test_messages)

    try:
        # Publish messages with delays
        for i, msg in enumerate(test_messages):
            # Publish to Redis
            channel = f"scan:{TEST_SCAN_ID}"
            subscribers = await redis_client.publish(channel, json.dumps(msg))
            print(f"   [{i+1}/{expected_count}] Published: {msg['status']} - {msg['progress']:.1f}% ({subscribers} subscribers)")

            # Wait for WebSocket to receive it
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)

                if data.get('type') == 'scan_update':
                    received_count += 1
                    print(f"   ✅ Received: {data.get('status')} - {data.get('progress', 0):.1f}%")
                else:
                    print(f"   ⚠️  Unexpected message type: {data.get('type')}")

            except asyncio.TimeoutError:
                print(f"   ❌ Timeout waiting for message {i+1}")
            except Exception as e:
                print(f"   ❌ Error receiving message: {e}")

            # Small delay between messages
            await asyncio.sleep(0.5)

    except Exception as e:
        print(f"❌ Error during message publishing: {e}")
        await websocket.close()
        await redis_client.close()
        return False

    # Step 5: Summary
    print()
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Messages published: {expected_count}")
    print(f"Messages received:  {received_count}")
    print()

    success = received_count == expected_count

    if success:
        print("✅ ALL TESTS PASSED - WebSocket flow working correctly!")
        print()
        print("🎉 Your WebSocket setup is working end-to-end:")
        print("   ✓ Redis pub/sub operational")
        print("   ✓ WebSocket endpoint accepting connections")
        print("   ✓ Messages flowing from publisher to subscriber")
        print()
        print("💡 Next steps:")
        print("   1. Restart your Docker containers to pick up the Redis hostname fix")
        print("   2. Try running a scan from the frontend")
        print("   3. The progress bar should now update in real-time!")
    else:
        print(f"❌ TESTS FAILED - Only {received_count}/{expected_count} messages received")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check backend logs: docker-compose logs backend")
        print("   2. Verify Redis connection: docker-compose logs redis")
        print("   3. Check for errors in the scanner_websocket.py handler")

    print()

    # Cleanup
    await websocket.close()
    await redis_client.close()

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(test_complete_flow())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
