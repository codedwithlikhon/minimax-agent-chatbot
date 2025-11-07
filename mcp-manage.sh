#!/bin/bash
# MiniMax Agent Chatbot - MCP Services Manager
# Comprehensive service management for all MCP Docker services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        🤖 MiniMax Agent Chatbot - MCP Services Manager      ║"
    echo "║                                                              ║"
    echo "║  🕐 MCP Time           🕸️ MCP Playwright                   ║"
    echo "║  🧠 MCP Thinking       🔍 MCP DuckDuckGo                    ║"
    echo "║  🤖 MCP Puppeteer      🧠 MCP Memory                        ║"
    echo "║  🖥️ Desktop Commander  🌐 VNC Desktop                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# MCP Service Configuration
declare -A MCP_SERVICES=(
    ["mcp-time"]="8001:mcp/time:latest"
    ["mcp-playwright"]="8002:mcp/playwright:latest"
    ["mcp-sequentialthinking"]="8003:mcp/sequentialthinking:latest"
    ["mcp-duckduckgo"]="8004:mcp/duckduckgo:latest"
    ["mcp-puppeteer"]="8005:mcp/puppeteer:latest"
    ["mcp-memory"]="8006:mcp/memory:latest"
    ["mcp-desktop-commander"]="8007:mcp/desktop-commander:latest"
    ["vnc-server"]="5900:consol/ubuntu-xfce-vnc"
    ["websockify"]="8080:novnc/websockify:latest"
    ["chatbot-api"]="8000:5173:."
)

# Service Health Check
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=5
    local attempt=1
    
    echo -e "${BLUE}Checking $service_name health (port $port)...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is healthy on port $port${NC}"
            return 0
        elif [ "$service_name" = "mcp-playwright" ] || [ "$service_name" = "mcp-sequentialthinking" ] || [ "$service_name" = "mcp-duckduckgo" ] || [ "$service_name" = "mcp-time" ]; then
            # MCP services use health endpoint
            if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ $service_name is healthy on port $port${NC}"
                return 0
            fi
        fi
        
        echo -e "${YELLOW}  Attempt $attempt/$max_attempts failed, retrying in 2 seconds...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}✗ $service_name health check failed on port $port${NC}"
    return 1
}

# Pull Docker images
pull_images() {
    echo -e "${BLUE}📥 Pulling Docker images...${NC}"
    
    for service_info in "${MCP_SERVICES[@]}"; do
        local image_name=$(echo $service_info | cut -d: -f3-)
        if [ "$image_name" != "." ]; then
            echo -e "${YELLOW}Pulling $image_name...${NC}"
            docker pull "$image_name" || echo -e "${RED}Failed to pull $image_name${NC}"
        fi
    done
    
    echo -e "${GREEN}✓ Docker images pull complete${NC}"
}

# Start Docker services
start_docker_services() {
    echo -e "${BLUE}🐳 Starting Docker services...${NC}"
    
    # Use docker-compose for orchestrated startup
    if [ -f "docker-compose.yml" ]; then
        echo -e "${YELLOW}Starting services with docker-compose...${NC}"
        docker-compose up -d
    else
        echo -e "${RED}docker-compose.yml not found${NC}"
        return 1
    fi
    
    # Wait for services to start
    echo -e "${YELLOW}Waiting for services to initialize...${NC}"
    sleep 10
}

# Stop Docker services
stop_docker_services() {
    echo -e "${RED}🛑 Stopping Docker services...${NC}"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
    else
        # Stop individual containers
        for service_name in "${!MCP_SERVICES[@]}"; do
            docker stop "$service_name" 2>/dev/null || true
            docker rm "$service_name" 2>/dev/null || true
        done
    fi
    
    echo -e "${GREEN}✓ Docker services stopped${NC}"
}

# Check all service health
check_all_services() {
    echo -e "${BLUE}🔍 Checking all service health...${NC}"
    echo "=============================================="
    
    local total_services=0
    local healthy_services=0
    
    for service_name in "${!MCP_SERVICES[@]}"; do
        total_services=$((total_services + 1))
        local port=$(echo ${MCP_SERVICES[$service_name]} | cut -d: -f1)
        
        if check_service_health "$service_name" "$port"; then
            healthy_services=$((healthy_services + 1))
        else
            echo -e "${RED}Service $service_name failed health check${NC}"
        fi
        echo ""
    done
    
    echo "=============================================="
    echo -e "${BLUE}Health Check Summary:${NC}"
    echo -e "Healthy: ${GREEN}$healthy_services${NC}/$total_services"
    
    if [ $healthy_services -eq $total_services ]; then
        echo -e "${GREEN}✓ All services are healthy!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some services are not healthy${NC}"
        return 1
    fi
}

# Start native services (without Docker)
start_native_services() {
    echo -e "${BLUE}🔧 Starting native services...${NC}"
    
    # Start VNC server
    if ! command -v x11vnc &> /dev/null; then
        echo -e "${YELLOW}Installing VNC server...${NC}"
        pkg install -y tigervnc
    fi
    
    # Set up VNC password
    if [ ! -f "$HOME/.vnc/passwd" ]; then
        echo -e "${YELLOW}Setting up VNC password...${NC}"
        echo "123456" | vncpasswd -f > $HOME/.vnc/passwd 2>/dev/null
    fi
    
    # Start VNC server
    export DISPLAY=:1
    nohup x11vnc -display :1 -rfbport 5900 -forever > logs/vnc.log 2>&1 &
    echo $! > pids/vnc.pid
    echo -e "${GREEN}✓ VNC server started on port 5900${NC}"
    
    # Start Chrome CDP server
    if command -v google-chrome &> /dev/null; then
        nohup google-chrome \
            --headless \
            --remote-debugging-port=9222 \
            --no-sandbox \
            --disable-gpu \
            --disable-web-security > logs/chrome.log 2>&1 &
        echo $! > pids/chrome.pid
        echo -e "${GREEN}✓ Chrome CDP started on port 9222${NC}"
    else
        echo -e "${YELLOW}Chrome not found, skipping CDP server${NC}"
    fi
    
    # Note: MCP services would need to be run separately
    echo -e "${YELLOW}Note: MCP services need Docker or separate installation${NC}"
}

# Show service status
show_status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo "=============================================="
    
    # Check docker services
    if command -v docker &> /dev/null; then
        echo -e "${BLUE}Docker Services:${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(mcp|vnc|websockify|chatbot)"
    else
        echo -e "${YELLOW}Docker not available${NC}"
    fi
    
    echo ""
    
    # Check port status
    echo -e "${BLUE}Port Status:${NC}"
    for service_name in "${!MCP_SERVICES[@]}"; do
        local port=$(echo ${MCP_SERVICES[$service_name]} | cut -d: -f1)
        if netstat -tuln 2>/dev/null | grep ":$port " >/dev/null; then
            echo -e "${service_name}: ${GREEN}● Port $port is open${NC}"
        else
            echo -e "${service_name}: ${RED}● Port $port is closed${NC}"
        fi
    done
}

# Setup development environment
setup_dev() {
    echo -e "${BLUE}🛠️ Setting up development environment...${NC}"
    
    # Create necessary directories
    mkdir -p logs pids data chrome_data
    
    # Install MCP service dependencies (if available)
    if command -v npm &> /dev/null; then
        npm install -g mcp-cli 2>/dev/null || echo -e "${YELLOW}MCP CLI not available${NC}"
    fi
    
    # Pull Docker images
    pull_images
    
    echo -e "${GREEN}✓ Development environment setup complete${NC}"
}

# Main functions
main() {
    case "${1:-start}" in
        "start")
            show_banner
            echo -e "${BLUE}🚀 Starting MiniMax Agent Chatbot with MCP services...${NC}"
            start_docker_services
            check_all_services
            
            echo -e "\n${GREEN}🎉 All services started!${NC}"
            echo -e "${BLUE}Access Points:${NC}"
            echo "  🌐 Web Interface: http://localhost:5173"
            echo "  🔗 API: http://localhost:8000"
            echo "  🕐 MCP Time: http://localhost:8001"
            echo "  🕸️ MCP Playwright: http://localhost:8002"
            echo "  🧠 MCP Thinking: http://localhost:8003"
            echo "  🔍 MCP Search: http://localhost:8004"
            echo "  🤖 MCP Puppeteer: http://localhost:8005"
            echo "  🧠 MCP Memory: http://localhost:8006"
            echo "  🖥️ Desktop Commander: http://localhost:8007"
            echo "  🖥️ VNC: localhost:5900"
            echo "  🌐 Websockify: http://localhost:8080"
            echo ""
            echo "📋 Examples:"
            echo "  • Chat: 'current time' / 'think about problem'"
            echo "  • Search: 'search python tutorials'"
            echo "  • Screenshot: 'screenshot web https://example.com'"
            echo "  • Status: './mcp-manage.sh status'"
            ;;
        
        "stop")
            show_banner
            echo -e "${RED}🛑 Stopping all services...${NC}"
            stop_docker_services
            echo -e "${GREEN}✓ All services stopped${NC}"
            ;;
        
        "restart")
            show_banner
            echo -e "${YELLOW}🔄 Restarting all services...${NC}"
            stop_docker_services
            sleep 3
            start_docker_services
            check_all_services
            ;;
        
        "status")
            show_banner
            show_status
            ;;
        
        "health")
            show_banner
            check_all_services
            ;;
        
        "setup")
            show_banner
            setup_dev
            ;;
        
        "logs")
            local service=${2:-"all"}
            echo -e "${BLUE}📋 Service Logs - $service${NC}"
            
            if [ "$service" = "all" ]; then
                docker-compose logs -f
            else
                docker-compose logs -f "$service"
            fi
            ;;
        
        "pull")
            show_banner
            pull_images
            ;;
        
        "native")
            show_banner
            echo -e "${BLUE}🔧 Starting with native services...${NC}"
            start_native_services
            ;;
        
        *)
            echo "Usage: $0 {start|stop|restart|status|health|setup|logs [service]|pull|native}"
            echo ""
            echo "Commands:"
            echo "  start   - Start all Docker services with health checks"
            echo "  stop    - Stop all Docker services"
            echo "  restart - Restart all services"
            echo "  status  - Show current service status"
            echo "  health  - Run comprehensive health checks"
            echo "  setup   - Setup development environment and pull images"
            echo "  logs    - Show logs (optionally specify service)"
            echo "  pull    - Pull Docker images only"
            echo "  native  - Start with native services (no Docker)"
            echo ""
            echo "MCP Services:"
            echo "  🕐 mcp-time           - Time and timezone service"
            echo "  🕸️ mcp-playwright     - Browser automation"
            echo "  🧠 mcp-thinking       - Sequential reasoning"
            echo "  🔍 mcp-duckduckgo     - Web search service"
            echo "  🤖 mcp-puppeteer      - Advanced browser automation"
            echo "  🧠 mcp-memory         - Memory management service"
            echo "  🖥️ mcp-desktop-commander - Desktop command execution"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"