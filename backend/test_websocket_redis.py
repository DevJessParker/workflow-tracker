#!/usr/bin/env python3
"""
Test script to verify WebSocket + Redis pub/sub workflow
Run this inside the Docker container
"""

import asyncio
import json
import redis.asyncio as aioredis


async def test_redis_pubsub():
    """Test async Redis pub/sub"""
    print("=== Testing Async Redis Pub/Sub ===")

    # Create async Redis clients
    publisher = aioredis.Redis(
        host='pinata-redis',
        port=6379,
        db=0,
        decode_responses=True
    )

    subscriber = aioredis.Redis(
        host='pinata-redis',
        port=6379,
        db=0,
        decode_responses=True
    )

    channel = "scan:test-scan-id"

    try:
        # Test connection
        print("1. Testing Redis connection...")
        await publisher.ping()
        print("   ✅ Redis connection OK")

        # Create pubsub
        print("2. Creating pubsub...")
        pubsub = subscriber.pubsub()
        print(f"   ✅ Pubsub created: {type(pubsub)}")

        # Subscribe
        print(f"3. Subscribing to channel: {channel}...")
        await pubsub.subscribe(channel)
        print("   ✅ Subscribed successfully")

        # Publish a test message
        print("4. Publishing test message...")
        test_data = {
            "scan_id": "test-scan-id",
            "status": "testing",
            "progress": 50.0,
            "message": "Test message"
        }
        subscribers = await publisher.publish(channel, json.dumps(test_data))
        print(f"   ✅ Published to {subscribers} subscriber(s)")

        # Listen for messages
        print("5. Listening for messages (5 second timeout)...")
        message_received = False

        async def listen_with_timeout():
            nonlocal message_received
            try:
                async for message in pubsub.listen():
                    print(f"   📨 Received: {message}")
                    if message['type'] == 'message':
                        data = json.loads(message['data'])
                        print(f"   ✅ Message data: {data}")
                        message_received = True
                        break
            except Exception as e:
                print(f"   ❌ Error listening: {e}")
                raise

        try:
            await asyncio.wait_for(listen_with_timeout(), timeout=5.0)
        except asyncio.TimeoutError:
            if not message_received:
                print("   ⏱️  Timeout - no message received")

        # Cleanup
        print("6. Cleaning up...")
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await publisher.close()
        await subscriber.close()
        print("   ✅ Cleanup complete")

        if message_received:
            print("\n✅ ALL TESTS PASSED - Redis pub/sub working correctly!")
            return True
        else:
            print("\n❌ TEST FAILED - Message not received")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_redis_pubsub())
    exit(0 if result else 1)
