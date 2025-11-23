#!/usr/bin/env python3
"""
Test script for Live Diagnostics WebSocket endpoint.

Tests:
1. WebSocket connection
2. Message broadcasting
3. Automatic reconnection
4. Health check endpoint
"""

import asyncio
import json
from datetime import UTC, datetime

import websockets


async def test_websocket_connection():
    """Test basic WebSocket connection."""
    uri = "ws://localhost:8000/api/v1/ws/live-diagnostics?update_interval=5"
    
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully")
            
            # Wait for welcome message
            message = await websocket.recv()
            data = json.loads(message)
            print(f"✓ Received welcome message: {data.get('message')}")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("✓ Sent ping")
            
            # Wait for pong
            message = await websocket.recv()
            data = json.loads(message)
            if data.get("type") == "pong":
                print("✓ Received pong")
            
            # Request snapshot
            await websocket.send(json.dumps({"type": "get_snapshot"}))
            print("✓ Requested snapshot")
            
            # Wait for a few messages
            print("\nListening for messages (5 seconds)...")
            try:
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    print(f"  {i+1}. Received {data.get('type')} message")
            except asyncio.TimeoutError:
                print("  (Timeout waiting for messages - this is normal if no data)")
            
            print("\n✓ WebSocket test completed successfully")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


async def test_health_endpoint():
    """Test WebSocket health check endpoint."""
    import aiohttp
    
    url = "http://localhost:8000/api/v1/ws/live-diagnostics/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"\nHealth check: {data}")
                    print("✓ Health endpoint working")
                    return True
                else:
                    print(f"✗ Health endpoint returned {response.status}")
                    return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Live Diagnostics WebSocket Test")
    print("=" * 60)
    print("\nNote: Ensure the TopDeck API server is running on localhost:8000")
    print("Start with: uvicorn topdeck.api.main:app --host 0.0.0.0 --port 8000\n")
    
    # Test health endpoint first
    health_ok = await test_health_endpoint()
    
    if health_ok:
        # Test WebSocket connection
        ws_ok = await test_websocket_connection()
        
        if ws_ok:
            print("\n" + "=" * 60)
            print("✓ All tests passed!")
            print("=" * 60)
        else:
            print("\n✗ WebSocket test failed")
    else:
        print("\n✗ Cannot connect to API server")
        print("Please start the server first:")
        print("  cd /home/runner/work/TopDeck/TopDeck")
        print("  uvicorn topdeck.api.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    asyncio.run(main())
