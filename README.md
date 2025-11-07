# MiniMax Agent Chatbot

A comprehensive AI-powered chatbot with todo management, XFCE desktop integration, and agentic task execution capabilities.

## 🌟 Features

### 🤖 **Intelligent Chat Interface**
- Natural language conversation with AI
- Real-time WebSocket communication
- Conversation history and memory
- Contextual responses and help

### ✅ **Todo Management System**
- Create, update, and delete todos
- Mark tasks as complete/incomplete
- Priority levels and timestamps
- Persistent SQLite database storage

### 🖥️ **XFCE Desktop Integration**
- Full XFCE desktop environment streaming
- VNC server for remote desktop access
- Screenshot capture capabilities
- Desktop control through chat commands

### 🏃 **Agentic Task Execution**
- Execute shell commands
- File system operations
- Web search and browsing
- Automated task scheduling
- Action result tracking

### 🌐 **Web Interface**
- Modern React-based chat UI
- Real-time todo dashboard
- Agent actions monitor
- Responsive design for mobile/desktop

### 🔗 **Multiple Service Architecture**
- **Web Frontend**: React chat interface (Port 5173)
- **API Server**: FastAPI backend (Port 8000)
- **🕐 MCP Time**: Time and timezone service (Port 8001)
- **🕸️ MCP Playwright**: Browser automation (Port 8002)
- **🧠 MCP Thinking**: Sequential reasoning (Port 8003)
- **🔍 MCP Search**: DuckDuckGo search (Port 8004)
- **VNC Server**: Desktop streaming (Port 5900)
- **Chrome CDP**: Browser automation (Port 9222)
- **Websockify**: VNC to WebSocket bridge (Port 8080)

### 🤖 **MCP (Model Context Protocol) Integration**
- **Time Management**: Get current time, timezone info, date calculations
- **Browser Automation**: Screenshot capture, web navigation, data extraction
- **Sequential Thinking**: Problem analysis, step-by-step reasoning
- **Web Search**: DuckDuckGo integration for instant answers and search results

## 🚀 Quick Start

### Method 1: Native Installation (Termux/Linux)

```bash
# Clone the repository
git clone <repository-url>
cd chatbot_project

# Install dependencies
pip install -r requirements.txt

# Start all services
chmod +x manage.sh
./manage.sh start

# Or use the Python launcher
python run.py
```

### Method 2: Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Method 3: Manual Service Startup

```bash
# Start backend API (Terminal 1)
python chatbot.py

# Start frontend server (Terminal 2)  
cd frontend && python -m http.server 5173

# Start VNC server (Terminal 3)
x11vnc -display :1 -rfbport 5900 -forever

# Start Chrome CDP (Terminal 4)
google-chrome --headless --remote-debugging-port=9222 --no-sandbox
```

## 📱 Access Points

### 🌐 **Web Interface**
- **URL**: http://localhost:5173
- **Description**: Main chat interface with todos, desktop control, and agent actions

### 🔗 **API Documentation**
- **URL**: http://localhost:8000/docs
- **Description**: Interactive API documentation and testing

### 🕐 **MCP Time Service**
- **URL**: http://localhost:8001
- **Description**: Time and timezone management service

### 🕸️ **MCP Playwright Service**
- **URL**: http://localhost:8002
- **Description**: Browser automation and screenshot service

### 🧠 **MCP Thinking Service**
- **URL**: http://localhost:8003
- **Description**: Sequential reasoning and analysis service

### 🔍 **MCP Search Service**
- **URL**: http://localhost:8004
- **Description**: DuckDuckGo search and instant answer service

### 🖥️ **VNC Desktop**
- **Host**: localhost
- **Port**: 5900
- **Password**: 123456
- **Description**: Access XFCE desktop environment

### 🌐 **Websockify Bridge**
- **URL**: http://localhost:8080
- **Description**: VNC to WebSocket bridge for web-based VNC client

### 🌐 **Chrome DevTools**
- **URL**: http://localhost:9222
- **Description**: Chrome DevTools Protocol interface

## 💬 Chat Commands

### Todo Management
```
add todo [task]              # Create a new todo
list todos                   # Show all todos
complete todo [id]           # Mark todo as complete
delete todo [id]             # Remove todo
```

### Agent Actions
```
execute command [command]     # Run shell command
search [query]               # Web search
file read [path]             # Read file content
file write [path] [content]  # Write to file
```

### Desktop Control
```
screenshot                   # Capture desktop screenshot
start desktop               # Launch XFCE session
show vnc                    # Display VNC connection info
open terminal               # Open terminal in desktop
```

### MCP Service Commands
```
current time [timezone]     # Get current time
time EST                    # Get time in specific timezone
think about [problem]       # Analyze problem with reasoning
analyze [question]          # Get detailed analysis
screenshot web [url]        # Take webpage screenshot
what is [question]          # Get instant answer
search [query]              # Enhanced web search
```

### General Conversation
```
help                        # Show available commands
status                      # Check service status
hello                       # Greeting response
```

## 🏗️ Architecture

### Backend Components

#### **FastAPI Server** (`chatbot.py`)
- RESTful API endpoints
- WebSocket real-time communication
- Session management
- Database operations

#### **Database Layer** (`Database` class)
- SQLite database management
- Todo, chat, and action storage
- Query optimization and indexing

#### **Chat Engine** (`ChatManager` class)
- Message processing
- Intent recognition
- Response generation
- Conversation history

#### **Agent Executor** (`AgentExecutor` class)
- Command execution
- File operations
- Web automation
- Action tracking

#### **XFCE Controller** (`XFCEController` class)
- Desktop environment management
- Screenshot capture
- VNC server control

### Frontend Components

#### **React Web Interface** (`index.html`)
- Chat message display
- Todo dashboard
- Agent actions monitor
- Real-time updates

#### **WebSocket Client**
- Real-time communication
- Message broadcasting
- Connection management

## 🛠️ Development

### Directory Structure
```
chatbot_project/
├── chatbot.py              # Main application
├── run.py                  # Startup script
├── manage.sh               # Service management
├── requirements.txt        # Python dependencies
├── .env                    # Configuration
├── Dockerfile              # Docker image
├── docker-compose.yml      # Docker orchestration
├── frontend/
│   └── index.html          # Web interface
├── logs/                   # Application logs
├── data/                   # Database and storage
└── pids/                   # Process IDs
```

### Configuration

Environment variables in `.env`:
- `DATABASE_PATH`: SQLite database location
- `WEB_PORT`: Frontend server port
- `API_PORT`: Backend API port
- `VNC_PORT`: Desktop streaming port
- `CHROME_CDP_PORT`: Browser automation port

### Service Management

```bash
# Check service status
./manage.sh status

# View logs
./manage.sh logs
./manage.sh logs api

# Health checks
./manage.sh health

# Stop all services
./manage.sh stop

# Restart services
./manage.sh restart
```

### MCP Service Management

```bash
# Start all MCP services
./mcp-manage.sh start

# Stop all MCP services
./mcp-manage.sh stop

# Check MCP service status
./mcp-manage.sh status

# Health check all MCP services
./mcp-manage.sh health

# Test MCP service integration
python test_mcp.py

# Setup development environment
./mcp-manage.sh setup
```

## 🔧 Customization

### Adding New Commands
Extend the `ChatBot` class in `chatbot.py`:

```python
async def _handle_custom_command(self, message: str) -> str:
    # Add your custom logic here
    return "Custom command response"
```

### Modifying Todo System
Update the `TodoManager` class to add:
- Categories and tags
- Due dates and reminders
- Priority levels
- File attachments

### Desktop Integration
Enhance the `XFCEController` class for:
- Application launching
- Window management
- System monitoring
- Custom automation

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill process on port
lsof -ti:8000 | xargs kill -9

# Or use the service manager
./manage.sh stop
```

#### VNC Connection Issues
- Check if VNC server is running: `netstat -tulpn | grep 5900`
- Verify password: Default is `123456`
- Check firewall settings

#### Chrome CDP Errors
- Ensure Chrome is installed: `google-chrome --version`
- Check Chrome process: `ps aux | grep chrome`
- Verify port accessibility: `curl http://localhost:9222`

#### Database Errors
```bash
# Reset database
rm chatbot.db
python run.py  # Will recreate database
```

### Log Analysis
```bash
# View recent logs
tail -f logs/chatbot.log

# Check service-specific logs
./manage.sh logs api
./manage.sh logs vnc
```

## 📊 Performance Monitoring

### Resource Usage
- Monitor CPU and memory usage
- Check database size and queries
- Track WebSocket connections
- Monitor disk space for logs

### Scaling Considerations
- Use Redis for session storage
- Implement message queuing
- Add load balancing
- Consider database migration to PostgreSQL

## 🔐 Security

### Current Security Measures
- Local development focus
- CORS configuration
- Input validation
- SQL injection prevention

### Production Recommendations
- Use environment variables for secrets
- Implement authentication
- Enable HTTPS
- Add rate limiting
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black *.py
flake8 *.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Termux project for Android Linux environment
- FastAPI for the excellent web framework
- XFCE for the lightweight desktop environment
- VNC for remote desktop capabilities
- React and Tailwind CSS for the modern UI

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Open an issue on GitHub
4. Contact the development team

---

**MiniMax Agent Chatbot** - Your intelligent assistant for productivity, automation, and desktop integration! 🤖✨