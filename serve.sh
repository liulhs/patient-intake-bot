#!/bin/bash

# OpenAI Tool Bot Service Manager - Simplified Version
# Manages both frontend (Next.js) and server (Python) services

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
SERVER_DIR="$SCRIPT_DIR/server"

# PID files
SERVER_PID_FILE="$SCRIPT_DIR/server.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/frontend.pid"

# Log files
SERVER_LOG="$SCRIPT_DIR/server.log"
FRONTEND_LOG="$SCRIPT_DIR/frontend.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if a service is running
is_running() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Start server service
start_server() {
    if is_running "$SERVER_PID_FILE"; then
        warning "Server is already running (PID: $(cat "$SERVER_PID_FILE"))"
        return 0
    fi

    log "Starting server service..."
    cd "$SERVER_DIR"
    
    if [[ ! -f "server.py" ]]; then
        error "server.py not found in $SERVER_DIR"
        return 1
    fi
    
    nohup python server.py > "$SERVER_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$SERVER_PID_FILE"
    
    sleep 2
    if is_running "$SERVER_PID_FILE"; then
        success "Server started (PID: $pid)"
    else
        error "Failed to start server"
        return 1
    fi
}

# Start frontend service
start_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        warning "Frontend is already running (PID: $(cat "$FRONTEND_PID_FILE"))"
        return 0
    fi

    log "Starting frontend service..."
    cd "$FRONTEND_DIR"
    
    nohup yarn dev > "$FRONTEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$FRONTEND_PID_FILE"
    
    sleep 2
    if is_running "$FRONTEND_PID_FILE"; then
        success "Frontend started (PID: $pid)"
    else
        error "Failed to start frontend"
        return 1
    fi
}

# Stop service
stop_service() {
    local service="$1"
    local pid_file
    local service_name
    
    case "$service" in
        "server")
            pid_file="$SERVER_PID_FILE"
            service_name="Server"
            ;;
        "frontend")
            pid_file="$FRONTEND_PID_FILE"
            service_name="Frontend"
            ;;
        *)
            error "Unknown service: $service"
            return 1
            ;;
    esac
    
    if [[ ! -f "$pid_file" ]]; then
        warning "$service_name is not running"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        log "Stopping $service_name (PID: $pid)..."
        kill "$pid"
        rm -f "$pid_file"
        success "$service_name stopped"
    else
        warning "$service_name was not running (stale PID file removed)"
        rm -f "$pid_file"
    fi
}

# Start both services
start_all() {
    log "Starting both services..."
    start_server
    start_frontend
    success "Both services started!"
}

# Stop both services
stop_all() {
    log "Stopping both services..."
    stop_service "server"
    stop_service "frontend"
    success "Both services stopped!"
}

# Show service status
show_status() {
    log "Service Status:"
    
    if is_running "$SERVER_PID_FILE"; then
        local server_pid=$(cat "$SERVER_PID_FILE")
        success "Server: Running (PID: $server_pid)"
    else
        error "Server: Not running"
    fi
    
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        success "Frontend: Running (PID: $frontend_pid)"
    else
        error "Frontend: Not running"
    fi
}

# Show logs
show_logs() {
    local service="$1"
    local lines="${2:-20}"
    
    case "$service" in
        "server")
            if [[ -f "$SERVER_LOG" ]]; then
                log "Server logs (last $lines lines):"
                tail -n "$lines" "$SERVER_LOG"
            else
                warning "Server log file not found"
            fi
            ;;
        "frontend")
            if [[ -f "$FRONTEND_LOG" ]]; then
                log "Frontend logs (last $lines lines):"
                tail -n "$lines" "$FRONTEND_LOG"
            else
                warning "Frontend log file not found"
            fi
            ;;
        *)
            error "Use 'server' or 'frontend'"
            return 1
            ;;
    esac
}

# Main command handling
case "$1" in
    "start")
        case "$2" in
            "server")
                start_server
                ;;
            "frontend")
                start_frontend
                ;;
            ""|"both")
                start_all
                ;;
            *)
                error "Unknown service: $2. Use 'server', 'frontend', or 'both'"
                exit 1
                ;;
        esac
        ;;
        
    "stop")
        case "$2" in
            "server")
                stop_service "server"
                ;;
            "frontend")
                stop_service "frontend"
                ;;
            ""|"both")
                stop_all
                ;;
            *)
                error "Unknown service: $2. Use 'server', 'frontend', or 'both'"
                exit 1
                ;;
        esac
        ;;
        
    "status")
        show_status
        ;;
        
    "logs")
        show_logs "$2" "$3"
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|logs} [service]"
        echo
        echo "Commands:"
        echo "  start [service]     - Start service(s)"
        echo "  stop [service]      - Stop service(s)"
        echo "  status              - Show service status"
        echo "  logs [service] [n]  - Show logs (default: 20 lines)"
        echo
        echo "Services:"
        echo "  server              - Python server (server.py)"
        echo "  frontend            - Next.js frontend (yarn dev)"
        echo "  both, (empty)       - Both services"
        echo
        echo "Examples:"
        echo "  $0 start            # Start both services"
        echo "  $0 start server     # Start only server"
        echo "  $0 stop both        # Stop both services"
        echo "  $0 logs server      # Show server logs"
        echo "  $0 status           # Show service status"
        exit 1
        ;;
esac