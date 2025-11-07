#!/bin/bash
# MiniMax Agent Chatbot - Service Manager
# Starts all required services with proper port configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Port configuration
PORTS=(5173 8000 8001 8002 8003 8004 8080 5900 9222)
SERVICE_NAMES=("Frontend" "API" "MCP-Time" "MCP-Playwright" "MCP-Thinking" "MCP-Search" "Websockify" "VNC" "Chrome CDP")

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    if check_port $port; then
        echo -e "${YELLOW}Killing process on port $port...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to start service
start_service() {
    local name=$1
    local command=$2
    local port=$3
    local log_file="logs/${name,,}.log"
    
    echo -e "${BLUE}Starting $name on port $port...${NC}"
    
    # Ensure logs directory exists
    mkdir -p logs
    
    # Kill any existing process on the port
    kill_port $port
    
    # Start service in background
    nohup $command > $log_file 2>&1 &
    local pid=$!
    echo $pid > "pids/${name,,}.pid"
    
    # Wait for service to start
    sleep 3
    
    if check_port $port; then
        echo -e "${GREEN}✓ $name started successfully (PID: $pid, Port: $port)${NC}"
        return 0
    else
        echo -e "${RED}✗ $name failed to start on port $port${NC}"
        return 1
    fi
}

# Function to stop service
stop_service() {
    local name=$1
    local pid_file="pids/${name,,}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
            kill $pid
            sleep 2
            
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid
            fi
        fi
        rm -f "$pid_file"
        echo -e "${GREEN}✓ $name stopped${NC}"
    else
        echo -e "${YELLOW}$name was not running${NC}"
    fi
}

# Function to start XFCE desktop environment
start_xfce() {
    echo -e "${BLUE}Starting XFCE Desktop Environment...${NC}"
    
    # Install required packages if not present
    if ! command -v xfce4-session &> /dev/null; then
        echo -e "${YELLOW}Installing XFCE packages...${NC}"
        pkg install -y xfce4 x11-repo termux-x11-nightly
    fi
    
    # Set up VNC server
    if ! command -v vncserver &> /dev/null; then
        echo -e "${YELLOW}Installing VNC server...${NC}"
        pkg install -y tigervnc
    fi
    
    # Start VNC server
    export DISPLAY=:1
    if [ ! -f "$HOME/.vnc/passwd" ]; then
        echo -e "${YELLOW}Setting up VNC password...${NC}"
        echo "123456" | vncpasswd -f > $HOME/.vnc/passwd 2>/dev/null
        vncserver -localhost
    fi
    
    # Start XFCE session
    nohup xfce4-session > logs/xfce.log 2>&1 &
    
    echo -e "${GREEN}✓ XFCE Desktop Environment started${NC}"
}

# Function to start sandbox services
start_sandbox() {
    echo -e "${BLUE}Starting Sandbox Services...${NC}"
    
    # Start Chrome in headless mode for CDP
    chrome_args=(
        --headless
        --remote-debugging-port=9222
        --no-sandbox
        --disable-gpu
        --disable-web-security
        --disable-features=VizDisplayCompositor
    )
    
    nohup google-chrome "${chrome_args[@]}" > logs/chrome.log 2>&1 &
    echo $! > pids/chrome.pid
    
    # Start VNC server for sandbox
    nohup x11vnc -display :1 -rfbport 5900 -forever > logs/vnc.log 2>&1 &
    echo $! > pids/vnc.pid
    
    sleep 3
    
    echo -e "${GREEN}✓ Sandbox Services started${NC}"
}

# Function to check service health
check_health() {
    local name=$1
    local port=$2
    local expected_pattern=$3
    
    echo -e "${BLUE}Checking $name health...${NC}"
    
    # Check port accessibility
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓ $name is responding on port $port${NC}"
        return 0
    else
        echo -e "${RED}✗ $name is not responding on port $port${NC}"
        return 1
    fi
}

# Main functions
start_all() {
    echo -e "${GREEN}🚀 Starting MiniMax Agent Chatbot Services...${NC}"
    echo "=============================================="
    
    # Create necessary directories
    mkdir -p logs pids
    
    # Start backend API
    start_service "API" "cd /workspace/chatbot_project && python chatbot.py" 8000
    
    # Start frontend (if serving static files)
    if [ -f "/workspace/chatbot_project/frontend/index.html" ]; then
        start_service "Frontend" "cd /workspace/chatbot_project/frontend && python -m http.server 5173" 5173
    fi
    
    # Start sandbox services
    start_sandbox
    
    # Health checks
    echo -e "\n${BLUE}Performing Health Checks...${NC}"
    sleep 5
    
    check_health "API" 8000
    check_health "Frontend" 5173
    check_health "VNC" 5900
    check_health "Chrome CDP" 9222
    
    echo -e "\n${GREEN}🎉 All services started!${NC}"
    echo -e "${BLUE}Access Points:${NC}"
    echo "  🌐 Web Interface: http://localhost:5173"
    echo "  🔗 API: http://localhost:8000"
    echo "  🖥️ VNC: localhost:5900"
    echo "  🌐 Chrome CDP: localhost:9222"
    echo ""
    echo "📋 Use 'npm run status' to check service status"
    echo "🛑 Use 'npm run stop' to stop all services"
}

stop_all() {
    echo -e "${RED}🛑 Stopping MiniMax Agent Chatbot Services...${NC}"
    echo "=============================================="
    
    # Stop services in reverse order
    stop_service "Frontend"
    stop_service "API"
    
    # Kill VNC and Chrome processes
    kill_port 5900
    kill_port 9222
    
    # Kill any remaining Chrome processes
    pkill -f "chrome" || true
    pkill -f "vnc" || true
    
    echo -e "${GREEN}✓ All services stopped${NC}"
}

status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo "=============================================="
    
    for i in "${!PORTS[@]}"; do
        port=${PORTS[$i]}
        name=${SERVICE_NAMES[$i]}
        
        if check_port $port; then
            echo -e "${name}: ${GREEN}● Running${NC} (Port: $port)"
        else
            echo -e "${name}: ${RED}● Stopped${NC} (Port: $port)"
        fi
    done
    
    echo ""
    
    # Check for running processes
    if [ -d "pids" ]; then
        echo -e "${BLUE}Running Processes:${NC}"
        for pid_file in pids/*.pid; do
            if [ -f "$pid_file" ]; then
                service_name=$(basename "$pid_file" .pid)
                pid=$(cat "$pid_file")
                
                if kill -0 $pid 2>/dev/null; then
                    echo -e "  ${service_name}: ${GREEN}PID $pid${NC}"
                else
                    echo -e "  ${service_name}: ${RED}PID $pid (dead)${NC}"
                    rm -f "$pid_file"
                fi
            fi
        done
    fi
}

logs() {
    local service=${1:-"all"}
    
    echo -e "${BLUE}📋 Service Logs${NC}"
    echo "=============================================="
    
    if [ ! -d "logs" ]; then
        echo "No logs directory found."
        return
    fi
    
    if [ "$service" = "all" ]; then
        for log_file in logs/*.log; do
            if [ -f "$log_file" ]; then
                echo -e "\n${BLUE}=== $(basename "$log_file") ===${NC}"
                tail -20 "$log_file"
            fi
        done
    else
        local log_file="logs/${service}.log"
        if [ -f "$log_file" ]; then
            echo -e "${BLUE}=== $service logs ===${NC}"
            tail -50 "$log_file"
        else
            echo "No logs found for $service"
        fi
    fi
}

# Parse command line arguments
case "${1:-start}" in
    "start")
        start_all
        ;;
    "stop")
        stop_all
        ;;
    "restart")
        stop_all
        sleep 2
        start_all
        ;;
    "status")
        status
        ;;
    "logs")
        logs "$2"
        ;;
    "health")
        check_health "API" 8000
        check_health "Frontend" 5173
        check_health "VNC" 5900
        check_health "Chrome CDP" 9222
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs [service]|health}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show service status"
        echo "  logs    - Show logs (optionally specify service)"
        echo "  health  - Check service health"
        exit 1
        ;;
esac