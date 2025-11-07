#!/usr/bin/env python3
"""
MiniMax Agent Chatbot - MCP Services Test Suite
Comprehensive testing for all MCP service integrations
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints
MCP_ENDPOINTS = {
    "time": "http://localhost:8001",
    "playwright": "http://localhost:8002", 
    "thinking": "http://localhost:8003",
    "search": "http://localhost:8004",
    "puppeteer": "http://localhost:8005",
    "memory": "http://localhost:8006",
    "desktop-commander": "http://localhost:8007",
    "chatbot": "http://localhost:8000"
}

class MCPTester:
    def __init__(self):
        self.results = {}
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, name: str, url: str, test_path: str = "/health") -> Dict:
        """Test a specific MCP service endpoint"""
        try:
            test_url = f"{url}{test_path}"
            async with self.session.get(test_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "name": name,
                        "url": url,
                        "status": "healthy",
                        "response": data,
                        "status_code": response.status,
                        "response_time": time.time()  # Will be calculated
                    }
                else:
                    return {
                        "name": name,
                        "url": url,
                        "status": f"error_{response.status}",
                        "status_code": response.status,
                        "response": await response.text()
                    }
        except asyncio.TimeoutError:
            return {
                "name": name,
                "url": url,
                "status": "timeout",
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "name": name,
                "url": url,
                "status": "error",
                "error": str(e)
            }
    
    async def test_time_service(self) -> Dict:
        """Test MCP Time service functionality"""
        try:
            url = f"{MCP_ENDPOINTS['time']}/api/time"
            params = {"timezone": "UTC", "format": "iso"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"status": "success", "data": data}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_search_service(self) -> Dict:
        """Test MCP DuckDuckGo search service"""
        try:
            url = f"{MCP_ENDPOINTS['search']}/api/search"
            params = {"q": "python programming", "max_results": 3}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"status": "success", "data": data}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_thinking_service(self) -> Dict:
        """Test MCP Sequential Thinking service"""
        try:
            url = f"{MCP_ENDPOINTS['thinking']}/api/think"
            data = {
                "problem": "How to build a chatbot",
                "max_steps": 3,
                "context": "Software development"
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"status": "success", "data": result}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_chatbot_integration(self) -> Dict:
        """Test chatbot integration with MCP services"""
        try:
            # Test MCP services status endpoint
            url = f"{MCP_ENDPOINTS['chatbot']}/api/mcp/services"
            async with self.session.get(url) as response:
                if response.status == 200:
                    services = await response.json()
                    return {"status": "success", "services": services}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def run_all_tests(self) -> Dict:
        """Run all MCP service tests"""
        print("🧪 Starting MCP Services Test Suite")
        print("=" * 50)
        
        results = {
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Test basic connectivity
        print("1. 🔍 Testing basic connectivity...")
        for service_name, url in MCP_ENDPOINTS.items():
            print(f"   Testing {service_name} ({url})...")
            result = await self.test_endpoint(service_name, url)
            results["tests"][f"{service_name}_connectivity"] = result
            
            if result["status"] == "healthy":
                print(f"   ✓ {service_name}: Healthy")
            else:
                print(f"   ✗ {service_name}: {result['status']}")
        
        # Test specific functionality
        print("\n2. ⚡ Testing specific functionality...")
        
        # Time service
        if results["tests"]["time_connectivity"]["status"] == "healthy":
            print("   Testing time service...")
            time_result = await self.test_time_service()
            results["tests"]["time_functionality"] = time_result
            
            if time_result["status"] == "success":
                print("   ✓ Time service: Functional")
            else:
                print(f"   ✗ Time service: {time_result['message']}")
        
        # Search service
        if results["tests"]["search_connectivity"]["status"] == "healthy":
            print("   Testing search service...")
            search_result = await self.test_search_service()
            results["tests"]["search_functionality"] = search_result
            
            if search_result["status"] == "success":
                print("   ✓ Search service: Functional")
            else:
                print(f"   ✗ Search service: {search_result['message']}")
        
        # Thinking service
        if results["tests"]["thinking_connectivity"]["status"] == "healthy":
            print("   Testing thinking service...")
            thinking_result = await self.test_thinking_service()
            results["tests"]["thinking_functionality"] = thinking_result
            
            if thinking_result["status"] == "success":
                print("   ✓ Thinking service: Functional")
            else:
                print(f"   ✗ Thinking service: {thinking_result['message']}")
        
        # Chatbot integration
        if results["tests"]["chatbot_connectivity"]["status"] == "healthy":
            print("   Testing chatbot integration...")
            integration_result = await self.test_chatbot_integration()
            results["tests"]["chatbot_integration"] = integration_result
            
            if integration_result["status"] == "success":
                print("   ✓ Chatbot integration: Working")
            else:
                print(f"   ✗ Chatbot integration: {integration_result['message']}")
        
        return results
    
    def print_summary(self, results: Dict):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(results["tests"])
        passed_tests = 0
        
        for test_name, result in results["tests"].items():
            if result["status"] in ["healthy", "success", "working"]:
                status_symbol = "✓"
                status_color = "green"
                passed_tests += 1
            else:
                status_symbol = "✗"
                status_color = "red"
            
            print(f"{status_symbol} {test_name.replace('_', ' ').title()}")
        
        print(f"\nResults: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All MCP services are working correctly!")
        else:
            print(f"⚠️ {total_tests - passed_tests} services need attention")
    
    def save_results(self, results: Dict, filename: str = "mcp_test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"💾 Test results saved to {filename}")

async def main():
    """Main test function"""
    print("🚀 MiniMax Agent Chatbot - MCP Services Test")
    print("This script tests all MCP service integrations\n")
    
    async with MCPTester() as tester:
        results = await tester.run_all_tests()
        tester.print_summary(results)
        tester.save_results(results)
        
        # Return exit code based on results
        failed_tests = sum(1 for result in results["tests"].values() 
                          if result["status"] not in ["healthy", "success", "working"])
        
        if failed_tests > 0:
            print(f"\n❌ {failed_tests} tests failed. Check service logs.")
            return 1
        else:
            print("\n✅ All tests passed! MCP services are ready.")
            return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)