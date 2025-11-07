#!/usr/bin/env python3
"""
MiniMax Agent Chatbot - Main Startup Script
Comprehensive chatbot with todos, XFCE display streaming, and agentic capabilities
"""

import os
import sys
import asyncio
import subprocess
import threading
import time
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our chatbot modules
try:
    from chatbot import app, chatbot, uvicorn
    print("✓ Chatbot modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import chatbot modules: {e}")
    sys.exit(1)

class ServiceManager:
    def __init__(self):
        self.services = {}
        self.processes = {}
        
    def start_frontend_server(self):
        """Start the static file server for frontend"""
        frontend_path = Path(__file__).parent / "frontend"
        if frontend_path.exists():
            try:
                import http.server
                import socketserver
                
                class Handler(http.server.SimpleHTTPRequestHandler):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, directory=str(frontend_path), **kwargs)
                
                with socketserver.TCPServer(("0.0.0.0", 5173), Handler) as httpd:
                    print(f"🌐 Frontend server running on port 5173")
                    httpd.serve_forever()
            except Exception as e:
                print(f"✗ Frontend server error: {e}")
        
    def start_api_server(self):
        """Start the FastAPI backend server"""
        try:
            uvicorn.run(
                "chatbot:app",
                host="0.0.0.0",
                port=8000,
                reload=True,
                log_level="info"
            )
        except Exception as e:
            print(f"✗ API server error: {e}")
    
    def start_sandbox_services(self):
        """Start sandbox services (VNC, Chrome CDP)"""
        try:
            # Start VNC server
            vnc_process = subprocess.Popen([
                "x11vnc", 
                "-display", ":1", 
                "-rfbport", "5900", 
                "-forever"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.processes["vnc"] = vnc_process
            print("🖥️ VNC server started on port 5900")
            
            # Start Chrome in headless mode for CDP
            chrome_process = subprocess.Popen([
                "google-chrome",
                "--headless",
                "--remote-debugging-port=9222",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-web-security"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.processes["chrome"] = chrome_process
            print("🌐 Chrome CDP server started on port 9222")
            
        except FileNotFoundError as e:
            print(f"⚠️ VNC/Chrome not found: {e}")
            print("   Install with: pkg install tigervnc google-chrome")
    
    def stop_services(self):
        """Stop all running services"""
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✓ {name} service stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"✓ {name} service force stopped")
            except Exception as e:
                print(f"✗ Error stopping {name}: {e}")
        
        self.processes.clear()
    
    def run_health_checks(self):
        """Run service health checks"""
        import requests
        
        services = {
            "API": "http://localhost:8000",
            "Frontend": "http://localhost:5173",
            "Chrome CDP": "http://localhost:9222/json"
        }
        
        print("\n🔍 Running health checks...")
        
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✓ {name}: Healthy")
                else:
                    print(f"⚠️ {name}: Status {response.status_code}")
            except Exception as e:
                print(f"✗ {name}: Error - {e}")
        
        # Check VNC port
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5900))
            if result == 0:
                print("✓ VNC: Port 5900 is open")
            else:
                print("✗ VNC: Port 5900 is not accessible")
            sock.close()
        except Exception as e:
            print(f"✗ VNC check error: {e}")

def display_banner():
    """Display startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🤖 MiniMax Agent Chatbot - Complete Implementation     ║
║                                                              ║
║  📝 Todo Management    🖥️ XFCE Display Streaming          ║
║  🏃 Agentic Actions    🤖 AI-Powered Chat                  ║
║  🌐 Web Interface      🔗 Real-time API                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def display_service_info():
    """Display service information"""
    services = """
🎯 Service Configuration:
┌─────────────────────────────────────────────────────────────┐
│ Service          │ Port  │ Description                    │
├─────────────────────────────────────────────────────────────┤
│ 🌐 Web Frontend  │ 5173  │ React Chat Interface           │
│ 🔗 API Server    │ 8000  │ FastAPI Backend                │
│ 🖥️ VNC Server    │ 5900  │ XFCE Desktop Streaming         │
│ 🌐 Chrome CDP    │ 9222  │ Browser Automation API         │
│ 🏗️ Sandbox API   │ 8080  │ Additional Sandbox Services    │
└─────────────────────────────────────────────────────────────┘

🚀 Quick Commands:
  • Access Web Interface: http://localhost:5173
  • API Documentation: http://localhost:8000/docs
  • VNC Connection: localhost:5900 (password: 123456)
  • Chrome DevTools: http://localhost:9222

💬 Chat Examples:
  • "add todo buy groceries"
  • "execute command ls -la"
  • "search python tutorials"
  • "take screenshot"
  • "help"

🛠️ Development:
  • Backend reload: Enabled (auto-restart on changes)
  • Database: SQLite (chatbot.db)
  • Logs: Check service output for details
    """
    print(services)

def main():
    """Main startup function"""
    display_banner()
    
    # Check if required packages are installed
    required_packages = ["fastapi", "uvicorn", "websockets"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️ Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Initialize database
    try:
        chatbot.db.init_database()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)
    
    # Start services
    service_manager = ServiceManager()
    
    try:
        # Start sandbox services in background
        sandbox_thread = threading.Thread(
            target=service_manager.start_sandbox_services,
            daemon=True
        )
        sandbox_thread.start()
        
        # Start API server in main thread
        print("🚀 Starting services...")
        print("   (Press Ctrl+C to stop all services)")
        print()
        
        display_service_info()
        print("\n" + "="*60)
        
        # Health checks after short delay
        def delayed_health_check():
            time.sleep(5)
            service_manager.run_health_checks()
        
        health_thread = threading.Thread(target=delayed_health_check, daemon=True)
        health_thread.start()
        
        # Start API server (this will block)
        service_manager.start_api_server()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"\n✗ Startup error: {e}")
        sys.exit(1)
    finally:
        print("\n🧹 Cleaning up services...")
        service_manager.stop_services()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    main()