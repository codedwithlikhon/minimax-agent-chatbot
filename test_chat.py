#!/usr/bin/env python3
"""
Test script for the MiniMax Agent Chatbot
Tests basic chat functionality
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_chat():
    """Test WebSocket chat functionality"""
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/ws/chat"
        print(f"Connecting to WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connection established")
            
            # Test message
            test_message = "Hello, can you help me with my todos?"
            print(f"Sending message: {test_message}")
            
            await websocket.send(test_message)
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"Received response: {response}")
            
            # Test second message
            test_message2 = "add todo test task"
            print(f"Sending message: {test_message2}")
            
            await websocket.send(test_message2)
            
            response2 = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"Received response: {response2}")
            
            print("✓ Chat functionality test passed!")
            return True
            
    except asyncio.TimeoutError:
        print("✗ Timeout waiting for response")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_api_endpoints():
    """Test basic API endpoints"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test MCP services endpoint
            async with session.get("http://localhost:8000/api/mcp/services") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ MCP services endpoint: {len(data)} services")
                else:
                    print(f"✗ MCP services endpoint: HTTP {resp.status}")
            
            # Test todos endpoint
            async with session.get("http://localhost:8000/api/todos") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ Todos endpoint: {len(data)} todos")
                else:
                    print(f"✗ Todos endpoint: HTTP {resp.status}")
                    
            # Test status endpoint
            async with session.get("http://localhost:8000/api/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✓ Status endpoint: OK")
                else:
                    print(f"✗ Status endpoint: HTTP {resp.status}")
                    
            return True
    except Exception as e:
        print(f"✗ API test error: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing MiniMax Agent Chatbot")
    print("=" * 50)
    
    # Test WebSocket chat
    print("1. Testing WebSocket chat functionality...")
    websocket_ok = await test_websocket_chat()
    
    print("\n2. Testing API endpoints...")
    api_ok = await test_api_endpoints()
    
    print("\n" + "=" * 50)
    if websocket_ok and api_ok:
        print("🎉 All tests passed! Chatbot is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)