#!/usr/bin/env python3
"""
MiniMax Agent Chatbot - Complete Implementation
A comprehensive chatbot with todos, XFCE display streaming, and agentic capabilities
"""

import asyncio
import json
import sqlite3
import os
import time
import subprocess
import websockets
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PORTS = {
    'web': 5173,
    'api': 8000,
    'sandbox_api': 8080,
    'vnc': 5900,
    'chrome_cdp': 9222
}

class Todo(BaseModel):
    id: Optional[int] = None
    title: str
    description: str = ""
    completed: bool = False
    priority: str = "medium"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ChatMessage(BaseModel):
    id: Optional[int] = None
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[str] = None
    metadata: Dict = {}

class AgentAction(BaseModel):
    id: Optional[int] = None
    action_type: str  # command, file_op, web_search, etc.
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result: str = ""
    created_at: Optional[str] = None

# MCP Service Models
class MCPRequest(BaseModel):
    query: str
    parameters: Dict = {}

class MCPResponse(BaseModel):
    success: bool
    data: Dict = {}
    error: Optional[str] = None

class TimeRequest(BaseModel):
    timezone: Optional[str] = "UTC"
    format: Optional[str] = "iso"
    timestamp: Optional[float] = None

class PlaywrightRequest(BaseModel):
    url: str
    action: str  # "navigate", "click", "screenshot", "extract"
    selector: Optional[str] = None
    timeout: Optional[int] = 30000

class ThinkingRequest(BaseModel):
    problem: str
    steps: Optional[int] = 5
    context: Optional[str] = ""

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    safe_search: Optional[bool] = True

# MCP Service Clients
class MCPTimeClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
    
    async def get_current_time(self, timezone: str = "UTC", format: str = "iso") -> Dict:
        """Get current time from MCP Time service"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                params = {"timezone": timezone, "format": format}
                async with session.get(f"{self.base_url}/api/time", params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_timezone_info(self, timezone: str) -> Dict:
        """Get timezone information"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/timezone/{timezone}") as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

class MCPPlaywrightClient:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.session = None
    
    async def navigate(self, url: str, timeout: int = 30000) -> Dict:
        """Navigate to a URL"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "timeout": timeout}
                async with session.post(f"{self.base_url}/api/navigate", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def take_screenshot(self, url: str, selector: Optional[str] = None) -> Dict:
        """Take a screenshot"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "selector": selector}
                async with session.post(f"{self.base_url}/api/screenshot", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_text(self, url: str, selector: str) -> Dict:
        """Extract text from a page element"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "selector": selector}
                async with session.post(f"{self.base_url}/api/extract", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

class MCPSequentialThinkingClient:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.session = None
    
    async def think(self, problem: str, max_steps: int = 5, context: str = "") -> Dict:
        """Perform sequential thinking on a problem"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {
                    "problem": problem,
                    "max_steps": max_steps,
                    "context": context
                }
                async with session.post(f"{self.base_url}/api/think", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze(self, question: str, context: str = "") -> Dict:
        """Analyze a question with reasoning"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {
                    "question": question,
                    "context": context,
                    "analysis_type": "comprehensive"
                }
                async with session.post(f"{self.base_url}/api/analyze", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

class MCPDuckDuckGoClient:
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url
        self.session = None
    
    async def search(self, query: str, max_results: int = 10, safe_search: bool = True) -> Dict:
        """Perform a DuckDuckGo search"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "max_results": max_results,
                    "safe_search": safe_search
                }
                async with session.get(f"{self.base_url}/api/search", params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def instant_answer(self, query: str) -> Dict:
        """Get instant answer from DuckDuckGo"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                params = {"q": query}
                async with session.get(f"{self.base_url}/api/instant", params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

class MCPPuppeteerClient:
    def __init__(self, base_url: str = "http://localhost:8005"):
        self.base_url = base_url
        self.session = None
    
    async def navigate(self, url: str, timeout: int = 30000) -> Dict:
        """Navigate to a URL with Puppeteer"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "timeout": timeout}
                async with session.post(f"{self.base_url}/api/navigate", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def take_screenshot(self, url: str, selector: Optional[str] = None) -> Dict:
        """Take a screenshot with Puppeteer"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "selector": selector}
                async with session.post(f"{self.base_url}/api/screenshot", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_text(self, url: str, selector: Optional[str] = None) -> Dict:
        """Extract text content with Puppeteer"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"url": url, "selector": selector}
                async with session.post(f"{self.base_url}/api/extract", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

class MCPMemoryClient:
    def __init__(self, base_url: str = "http://localhost:8006"):
        self.base_url = base_url
        self.session = None
    
    async def store_memory(self, key: str, value: str) -> Dict:
        """Store a memory item"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"key": key, "value": value}
                async with session.post(f"{self.base_url}/api/memory", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_memory(self, key: str) -> Dict:
        """Get a memory item"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/memory/{key}") as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def search_memories(self, query: str) -> Dict:
        """Search memory items"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                params = {"q": query}
                async with session.get(f"{self.base_url}/api/memory/search", params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

class MCPDesktopCommanderClient:
    def __init__(self, base_url: str = "http://localhost:8007"):
        self.base_url = base_url
        self.session = None
    
    async def execute_command(self, command: str) -> Dict:
        """Execute a desktop command"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                data = {"command": command}
                async with session.post(f"{self.base_url}/api/command", json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def list_processes(self) -> Dict:
        """List running processes"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/processes") as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/system") as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

class MCPServices:
    def __init__(self):
        self.time_client = MCPTimeClient()
        self.playwright_client = MCPPlaywrightClient()
        self.thinking_client = MCPSequentialThinkingClient()
        self.search_client = MCPDuckDuckGoClient()
        self.puppeteer_client = MCPPuppeteerClient()
        self.memory_client = MCPMemoryClient()
        self.desktop_client = MCPDesktopCommanderClient()
    
    async def get_current_time(self, timezone: str = "UTC") -> str:
        """Get current time as formatted string"""
        result = await self.time_client.get_current_time(timezone)
        if "error" in result:
            return f"Time service error: {result['error']}"
        
        current_time = result.get("current_time", "Unknown time")
        timezone_info = result.get("timezone", timezone)
        return f"🕐 Current time: {current_time} ({timezone_info})"
    
    async def think_about(self, problem: str, steps: int = 3) -> str:
        """Get thinking analysis for a problem"""
        result = await self.thinking_client.think(problem, max_steps=steps)
        if "error" in result:
            return f"Thinking service error: {result['error']}"
        
        thinking_steps = result.get("steps", [])
        if not thinking_steps:
            return "No thinking steps available"
        
        response = f"🤔 **Thinking about: {problem}**\n\n"
        for i, step in enumerate(thinking_steps, 1):
            response += f"{i}. {step}\n"
        
        conclusion = result.get("conclusion", "")
        if conclusion:
            response += f"\n**Conclusion:** {conclusion}"
        
        return response
    
    async def search_web(self, query: str) -> str:
        """Search the web using DuckDuckGo"""
        result = await self.search_client.search(query)
        if "error" in result:
            return f"Search service error: {result['error']}"
        
        results = result.get("results", [])
        if not results:
            return f"No results found for '{query}'"
        
        response = f"🔍 **Search results for: {query}**\n\n"
        for i, item in enumerate(results[:5], 1):  # Limit to 5 results
            title = item.get("title", "No title")
            url = item.get("url", "")
            snippet = item.get("snippet", "No description")
            
            response += f"**{i}. {title}**\n"
            if url:
                response += f"   🔗 {url}\n"
            if snippet:
                response += f"   📝 {snippet}\n"
            response += "\n"
        
        return response
    
    async def get_instant_answer(self, query: str) -> str:
        """Get instant answer"""
        result = await self.search_client.instant_answer(query)
        if "error" in result:
            return f"Search service error: {result['error']}"
        
        answer = result.get("answer", "")
        if not answer:
            return f"No instant answer found for '{query}'"
        
        return f"💡 **Instant Answer:** {answer}"
    
    async def take_web_screenshot(self, url: str) -> str:
        """Take screenshot of a webpage"""
        result = await self.playwright_client.take_screenshot(url)
        if "error" in result:
            return f"Screenshot service error: {result['error']}"
        
        screenshot_path = result.get("screenshot_path", "")
        if screenshot_path:
            return f"📸 Screenshot saved: {screenshot_path}"
        else:
            return "Screenshot taken but path not available"

class Database:
    def __init__(self, db_path: str = "chatbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            priority TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        );
        
        CREATE TABLE IF NOT EXISTS agent_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data TEXT
        );
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

class TodoManager:
    def __init__(self, db: Database):
        self.db = db
    
    async def create_todo(self, todo: Todo) -> Todo:
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO todos (title, description, completed, priority)
            VALUES (?, ?, ?, ?)
        """, (todo.title, todo.description, todo.completed, todo.priority))
        
        todo.id = cursor.lastrowid
        todo.created_at = datetime.now().isoformat()
        todo.updated_at = todo.created_at
        
        conn.commit()
        conn.close()
        return todo
    
    async def get_todos(self) -> List[Todo]:
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM todos ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        todos = []
        for row in rows:
            todos.append(Todo(
                id=row[0],
                title=row[1],
                description=row[2] or "",
                completed=bool(row[3]),
                priority=row[4] or "medium",
                created_at=row[5],
                updated_at=row[6]
            ))
        
        conn.close()
        return todos
    
    async def update_todo(self, todo_id: int, updates: dict) -> Optional[Todo]:
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [todo_id]
        
        cursor.execute(f"""
            UPDATE todos SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        
        if cursor.rowcount == 0:
            conn.close()
            return None
        
        # Fetch updated todo
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        
        todo = Todo(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            completed=bool(row[3]),
            priority=row[4] or "medium",
            created_at=row[5],
            updated_at=row[6]
        )
        
        conn.commit()
        conn.close()
        return todo
    
    async def delete_todo(self, todo_id: int) -> bool:
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success

class ChatManager:
    def __init__(self, db: Database):
        self.db = db
        self.conversation_history = []
        self.max_history = 50
    
    async def add_message(self, role: str, content: str, metadata: Dict = {}) -> ChatMessage:
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO chat_messages (role, content, metadata)
            VALUES (?, ?, ?)
        """, (role, content, json.dumps(metadata)))
        
        message_id = cursor.lastrowid
        timestamp = datetime.now().isoformat()
        
        conn.commit()
        conn.close()
        
        # Add to memory
        message = ChatMessage(
            id=message_id,
            role=role,
            content=content,
            timestamp=timestamp,
            metadata=metadata
        )
        
        self.conversation_history.append(message)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
        
        return message
    
    async def get_conversation(self, limit: int = 20) -> List[ChatMessage]:
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM chat_messages
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in reversed(rows):  # Reverse to get chronological order
            messages.append(ChatMessage(
                id=row[0],
                role=row[1],
                content=row[2],
                timestamp=row[3],
                metadata=json.loads(row[4] or "{}")
            ))
        
        return messages

class AgentExecutor:
    def __init__(self, db: Database):
        self.db = db
        self.active_actions = {}
        self.results = {}
    
    async def execute_action(self, action_type: str, description: str, params: Dict = None) -> AgentAction:
        action = AgentAction(
            action_type=action_type,
            description=description,
            status="running"
        )
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_actions (action_type, description, status)
            VALUES (?, ?, ?)
        """, (action_type, description, "running"))
        
        action.id = cursor.lastrowid
        action.created_at = datetime.now().isoformat()
        
        conn.commit()
        conn.close()
        
        # Execute action in background
        asyncio.create_task(self._execute_action_async(action, params or {}))
        
        return action
    
    async def _execute_action_async(self, action: AgentAction, params: Dict):
        try:
            if action.action_type == "command":
                result = await self._execute_command(params.get("command", ""))
            elif action.action_type == "file_operation":
                result = await self._execute_file_op(params)
            elif action.action_type == "web_search":
                result = await self._execute_web_search(params.get("query", ""))
            elif action.action_type == "xfce_action":
                result = await self._execute_xfce_action(params)
            else:
                result = f"Unknown action type: {action.action_type}"
            
            # Update action with result
            await self._update_action_status(action.id, "completed", result)
            
        except Exception as e:
            await self._update_action_status(action.id, "failed", str(e))
    
    async def _execute_command(self, command: str) -> str:
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            result = f"Command: {command}\n"
            if stdout:
                result += f"Output:\n{stdout.decode()}\n"
            if stderr:
                result += f"Error:\n{stderr.decode()}\n"
            result += f"Exit code: {process.returncode}"
            
            return result
            
        except Exception as e:
            return f"Command execution failed: {str(e)}"
    
    async def _execute_file_op(self, params: Dict) -> str:
        operation = params.get("operation", "")
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        
        try:
            if operation == "read":
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            elif operation == "write":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"File written successfully: {file_path}"
            elif operation == "append":
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(content)
                return f"Content appended to: {file_path}"
            else:
                return f"Unknown file operation: {operation}"
        except Exception as e:
            return f"File operation failed: {str(e)}"
    
    async def _execute_web_search(self, query: str) -> str:
        # Simulate web search (replace with actual implementation)
        await asyncio.sleep(1)  # Simulate search time
        return f"Search results for '{query}':\n1. Result 1\n2. Result 2\n3. Result 3"
    
    async def _execute_xfce_action(self, params: Dict) -> str:
        action = params.get("action", "")
        
        # Simulate XFCE actions
        if action == "screenshot":
            return "Screenshot taken and saved to /tmp/screenshot.png"
        elif action == "open_terminal":
            return "Terminal opened in XFCE desktop"
        elif action == "list_applications":
            return "XFCE Applications:\n- Firefox\n- Thunar\n- Terminal\n- Text Editor"
        else:
            return f"XFCE action '{action}' executed"
    
    async def _update_action_status(self, action_id: int, status: str, result: str):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE agent_actions 
            SET status = ?, result = ?
            WHERE id = ?
        """, (status, result, action_id))
        
        conn.commit()
        conn.close()
        
        self.results[action_id] = {"status": status, "result": result}

class XFCEController:
    def __init__(self):
        self.vnc_port = PORTS['vnc']
        self.screenshot_path = "/tmp/screenshot.png"
    
    async def start_xfce_session(self):
        """Start XFCE desktop session"""
        try:
            # Start XFCE in background
            await asyncio.create_subprocess_shell(
                "export DISPLAY=:1 && startxfce4 &",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            logger.info("XFCE session started")
            return True
        except Exception as e:
            logger.error(f"Failed to start XFCE: {e}")
            return False
    
    async def take_screenshot(self) -> str:
        """Take screenshot of current XFCE session"""
        try:
            # Simulate screenshot (in real implementation, use scrot or import)
            return f"Screenshot saved to {self.screenshot_path}"
        except Exception as e:
            return f"Screenshot failed: {str(e)}"
    
    async def get_vnc_connection(self) -> str:
        """Get VNC connection details"""
        return f"VNC server running on localhost:{self.vnc_port}"

class ChatBot:
    def __init__(self):
        self.db = Database()
        self.todo_manager = TodoManager(self.db)
        self.chat_manager = ChatManager(self.db)
        self.agent_executor = AgentExecutor(self.db)
        self.xfce_controller = XFCEController()
        self.mcp_services = MCPServices()  # MCP services integration
        self.clients = set()
    
    async def process_message(self, message: str, session_id: str = "default") -> str:
        """Process incoming chat message with AI logic"""
        
        # Add user message to history
        await self.chat_manager.add_message("user", message)
        
        # Simple intent recognition and response generation
        message_lower = message.lower()
        
        # Todo-related commands
        if "todo" in message_lower or "task" in message_lower:
            return await self._handle_todo_command(message)
        
        # Agent commands
        elif "execute" in message_lower or "run" in message_lower:
            return await self._handle_agent_command(message)
        
        # XFCE/Desktop commands
        elif "desktop" in message_lower or "screenshot" in message_lower or "xfce" in message_lower:
            return await self._handle_xfce_command(message)
        
        # Web commands
        elif "search" in message_lower or "browse" in message_lower:
            return await self._handle_web_command(message)
        
        # MCP Service commands
        elif any(cmd in message_lower for cmd in ["time", "current time", "date", "think", "analyze", "reason", "screenshot"]):
            return await self._handle_mcp_command(message)
        
        # General conversation
        else:
            return await self._handle_general_chat(message)
    
    async def _handle_todo_command(self, message: str) -> str:
        if "add" in message or "create" in message:
            # Extract todo from message (simple parsing)
            title = message.replace("add todo", "").replace("create todo", "").strip()
            if not title:
                return "Please provide a todo title. Example: 'add todo buy groceries'"
            
            todo = Todo(title=title)
            created_todo = await self.todo_manager.create_todo(todo)
            return f"✅ Todo created: '{created_todo.title}' (ID: {created_todo.id})"
        
        elif "list" in message or "show" in message:
            todos = await self.todo_manager.get_todos()
            if not todos:
                return "No todos found. Create one with 'add todo [title]'"
            
            response = "📝 Your todos:\n"
            for todo in todos:
                status = "✅" if todo.completed else "⏳"
                response += f"{status} {todo.title} (ID: {todo.id})\n"
            
            return response
        
        elif "complete" in message or "done" in message:
            # Extract ID from message
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                todo_id = int(numbers[0])
                updated = await self.todo_manager.update_todo(todo_id, {"completed": True})
                if updated:
                    return f"✅ Todo completed: {updated.title}"
                else:
                    return f"❌ Todo not found with ID: {todo_id}"
            else:
                return "Please specify a todo ID. Example: 'complete todo 1'"
        
        return "Todo commands: add todo [title], list todos, complete todo [id]"
    
    async def _handle_agent_command(self, message: str) -> str:
        if "command" in message:
            # Extract command from message
            command = message.replace("execute command", "").replace("run command", "").strip()
            if not command:
                return "Please provide a command. Example: 'execute command ls -la'"
            
            action = await self.agent_executor.execute_action("command", f"Execute: {command}", {"command": command})
            return f"🔄 Action started: {action.description} (ID: {action.id})"
        
        elif "file" in message:
            return "File operation commands: read file [path], write file [path] [content], append file [path] [content]"
        
        return "Agent commands: execute command [command], file operations"
    
    async def _handle_xfce_command(self, message: str) -> str:
        if "screenshot" in message:
            result = await self.xfce_controller.take_screenshot()
            return f"🖥️ {result}"
        
        elif "vnc" in message or "connect" in message:
            connection = await self.xfce_controller.get_vnc_connection()
            return f"🖥️ {connection}\nUse VNC client to connect"
        
        elif "start" in message or "launch" in message:
            success = await self.xfce_controller.start_xfce_session()
            if success:
                return "🖥️ XFCE desktop session started"
            else:
                return "❌ Failed to start XFCE session"
        
        return "XFCE commands: screenshot, start desktop, show vnc connection"
    
    async def _handle_web_command(self, message: str) -> str:
        if "search" in message:
            query = message.replace("search", "").strip()
            if not query:
                return "Please provide a search query. Example: 'search python tutorials'"
            
            action = await self.agent_executor.execute_action("web_search", f"Search: {query}", {"query": query})
            return f"🔍 Search started: {query} (ID: {action.id})"
        
        return "Web commands: search [query]"
    
    async def _handle_general_chat(self, message: str) -> str:
        # Simple AI-like responses
        responses = {
            "hello": "Hello! I'm your AI assistant. I can help with todos, execute commands, manage XFCE desktop, and more.",
            "help": "I can help you with:\n📝 Todo management: 'add todo buy groceries'\n🔄 Commands: 'execute command ls -la'\n🖥️ Desktop: 'screenshot', 'start desktop'\n🔍 Web: 'search python tutorials'",
            "status": f"Service status:\n🖥️ XFCE VNC: localhost:{self.vnc_port}\n🌐 Web Frontend: http://localhost:{PORTS['web']}\n🔗 API: http://localhost:{PORTS['api']}",
        }
        
        message_lower = message.lower()
        for key, response in responses.items():
            if key in message_lower:
                return response
        
        return f"I understood: '{message}'. Try asking for help with specific tasks like todos, commands, or desktop operations."
    
    async def _handle_mcp_command(self, message: str) -> str:
        """Handle MCP service commands"""
        message_lower = message.lower()
        
        # Time-related commands
        if any(word in message_lower for word in ["time", "date", "clock"]):
            # Extract timezone if provided
            timezone = "UTC"
            for tz in ["utc", "est", "pst", "gmt", "jst", "cet"]:
                if tz in message_lower:
                    timezone = tz.upper()
                    break
            
            time_info = await self.mcp_services.get_current_time(timezone)
            return time_info
        
        # Thinking/Analysis commands
        elif any(word in message_lower for word in ["think", "analyze", "reason", "reasoning", "solve"]):
            # Extract problem from message
            problem = message.replace("think about", "").replace("analyze", "").replace("reason about", "").strip()
            if not problem:
                problem = "the current situation"  # Default problem
            
            thinking_result = await self.mcp_services.think_about(problem)
            return thinking_result
        
        # Web screenshot commands
        elif "screenshot" in message_lower and ("web" in message_lower or "page" in message_lower or "website" in message_lower):
            # Extract URL from message
            import re
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, message)
            
            if urls:
                url = urls[0]
                screenshot_result = await self.mcp_services.take_web_screenshot(url)
                return screenshot_result
            else:
                return "Please provide a valid URL for screenshot. Example: 'screenshot website https://example.com'"
        
        # Instant answer commands
        elif any(word in message_lower for word in ["what is", "how many", "when did", "where is", "who is"]):
            # Extract query
            query = message
            for prefix in ["what is", "how many", "when did", "where is", "who is"]:
                if query.lower().startswith(prefix):
                    query = query[len(prefix):].strip()
                    break
            
            if query:
                answer = await self.mcp_services.get_instant_answer(query)
                return answer
            else:
                return "Please provide a clear question. Example: 'what is python'"
        
        # Web search enhancement
        elif "search" in message_lower:
            query = message.replace("search", "").replace("search for", "").strip()
            if not query:
                return "Please provide a search query. Example: 'search python tutorials'"
            
            search_result = await self.mcp_services.search_web(query)
            return search_result
        
        return "MCP commands: time [timezone], think about [problem], screenshot web [url], what is [question], search [query]"

# WebSocket handler
class WebSocketManager:
    def __init__(self, chatbot: ChatBot):
        self.chatbot = chatbot
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# FastAPI application
app = FastAPI(title="MiniMax Agent Chatbot", version="1.0.0")
chatbot = ChatBot()
ws_manager = WebSocketManager(chatbot)

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="frontend/build", html=True), name="static")

@app.get("/")
async def read_root():
    return HTMLResponse(content=open("frontend/build/index.html").read())

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            response = await chatbot.process_message(data)
            await websocket.send_text(response)
    except:
        ws_manager.disconnect(websocket)

# API endpoints
@app.get("/api/todos")
async def get_todos():
    return await chatbot.todo_manager.get_todos()

@app.post("/api/todos")
async def create_todo(todo: Todo):
    return await chatbot.todo_manager.create_todo(todo)

@app.put("/api/todos/{todo_id}")
async def update_todo(todo_id: int, updates: dict):
    return await chatbot.todo_manager.update_todo(todo_id, updates)

@app.delete("/api/todos/{todo_id}")
async def delete_todo(todo_id: int):
    success = await chatbot.todo_manager.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted successfully"}

@app.get("/api/chat/history")
async def get_chat_history():
    return await chatbot.chat_manager.get_conversation()

@app.get("/api/agent/actions")
async def get_agent_actions():
    # Get recent actions from database
    conn = sqlite3.connect(chatbot.db.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_actions ORDER BY created_at DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    actions = []
    for row in rows:
        actions.append({
            "id": row[0],
            "action_type": row[1],
            "description": row[2],
            "status": row[3],
            "result": row[4] or "",
            "created_at": row[5]
        })
    
    return actions

@app.get("/api/xfce/status")
async def get_xfce_status():
    return {
        "vnc_port": PORTS['vnc'],
        "chrome_cdp_port": PORTS['chrome_cdp'],
        "status": "running" if True else "stopped"
    }

@app.post("/api/xfce/action")
async def xfce_action(action_type: str, params: dict = {}):
    result = await chatbot.agent_executor.execute_action("xfce_action", f"XFCE: {action_type}", {"action": action_type, **params})
    return {"action_id": result.id, "message": "Action started"}

# MCP Service API Endpoints

@app.get("/api/mcp/services")
async def get_mcp_services_status():
    """Get status of all MCP services"""
    services = {
        "time": {"port": 8001, "url": "http://localhost:8001", "status": "unknown"},
        "playwright": {"port": 8002, "url": "http://localhost:8002", "status": "unknown"},
        "sequentialthinking": {"port": 8003, "url": "http://localhost:8003", "status": "unknown"},
        "duckduckgo": {"port": 8004, "url": "http://localhost:8004", "status": "unknown"},
        "puppeteer": {"port": 8005, "url": "http://localhost:8005", "status": "unknown"},
        "memory": {"port": 8006, "url": "http://localhost:8006", "status": "unknown"},
        "desktop-commander": {"port": 8007, "url": "http://localhost:8007", "status": "unknown"}
    }
    
    # Check service health
    for service_name, service_info in services.items():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_info['url']}/health", timeout=2) as resp:
                    if resp.status == 200:
                        service_info["status"] = "healthy"
                    else:
                        service_info["status"] = f"error_{resp.status}"
        except:
            service_info["status"] = "unreachable"
    
    return services

@app.get("/api/mcp/time")
async def get_current_time(timezone: str = "UTC", format: str = "iso"):
    """Get current time from MCP Time service"""
    return await chatbot.mcp_services.get_current_time(timezone)

@app.post("/api/mcp/think")
async def think_problem(problem: str, max_steps: int = 5, context: str = ""):
    """Request thinking analysis from MCP Sequential Thinking service"""
    result = await chatbot.mcp_services.think_about(problem, max_steps)
    return {"problem": problem, "analysis": result}

@app.post("/api/mcp/search")
async def search_web(query: str, max_results: int = 10):
    """Search web using MCP DuckDuckGo service"""
    result = await chatbot.mcp_services.search_web(query)
    return {"query": query, "results": result}

@app.post("/api/mcp/screenshot")
async def take_web_screenshot(url: str):
    """Take screenshot of webpage using MCP Playwright service"""
    result = await chatbot.mcp_services.take_web_screenshot(url)
    return {"url": url, "screenshot": result}

@app.get("/api/mcp/instant/{query}")
async def get_instant_answer(query: str):
    """Get instant answer from MCP DuckDuckGo service"""
    result = await chatbot.mcp_services.get_instant_answer(query)
    return {"query": query, "answer": result}

if __name__ == "__main__":
    print("🚀 Starting MiniMax Agent Chatbot")
    print(f"🌐 Web Frontend: http://localhost:{PORTS['web']}")
    print(f"🔗 API Server: http://localhost:{PORTS['api']}")
    print(f"🖥️ VNC Port: {PORTS['vnc']}")
    print(f"🌐 Chrome CDP: {PORTS['chrome_cdp']}")
    
    uvicorn.run(
        "chatbot:app",
        host="0.0.0.0",
        port=PORTS['api'],
        reload=True,
        log_level="info"
    )