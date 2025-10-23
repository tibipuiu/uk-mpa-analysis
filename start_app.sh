#!/bin/bash

# MPA Flask App Startup Script
# Reliable startup with debugging and health checks

set -e  # Exit on any error

APP_DIR="/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app"
LOG_FILE="$APP_DIR/startup.log"
PID_FILE="$APP_DIR/app.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Step 1: Check if app is already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            warning "App already running with PID $PID"
            echo "Access at: http://127.0.0.1:5000"
            exit 0
        else
            log "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
}

# Step 2: Environment checks
check_environment() {
    log "Checking environment..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "python3 not found"
        exit 1
    fi
    
    # Check app directory
    if [ ! -d "$APP_DIR" ]; then
        error "App directory not found: $APP_DIR"
        exit 1
    fi
    
    # Check app.py exists
    if [ ! -f "$APP_DIR/app.py" ]; then
        error "app.py not found in $APP_DIR"
        exit 1
    fi
    
    success "Environment checks passed"
}

# Step 3: Dependency checks
check_dependencies() {
    log "Checking dependencies..."
    
    cd "$APP_DIR"
    
    # Test imports
    if ! python3 -c "import flask, pandas, gfwapiclient" 2>/dev/null; then
        error "Missing dependencies. Installing..."
        if [ -f "requirements.txt" ]; then
            pip3 install -r requirements.txt
        else
            pip3 install flask pandas gfw-api-python-client reportlab flask-cors
        fi
    fi
    
    success "Dependencies checked"
}

# Step 4: Port availability
check_port() {
    log "Checking port 5000..."
    
    if ss -tlnp | grep -q :5000; then
        error "Port 5000 already in use"
        ss -tlnp | grep :5000
        exit 1
    fi
    
    success "Port 5000 available"
}

# Step 5: Start the app
start_app() {
    log "Starting Flask app..."
    
    cd "$APP_DIR"
    
    # Start app in background
    nohup python3 app.py > flask_app.log 2>&1 &
    APP_PID=$!
    
    # Save PID
    echo $APP_PID > "$PID_FILE"
    
    log "App started with PID $APP_PID"
    
    # Wait for app to start
    sleep 3
    
    # Check if process is still running
    if ! ps -p $APP_PID > /dev/null; then
        error "App failed to start"
        cat flask_app.log
        exit 1
    fi
    
    success "App process running"
}

# Step 6: Health check
health_check() {
    log "Performing health check..."
    
    # Wait up to 30 seconds for app to be ready
    for i in {1..30}; do
        if curl -s http://127.0.0.1:5000/ > /dev/null 2>&1; then
            success "Health check passed"
            echo ""
            echo "=================================="
            echo "🚀 MPA Flask App is running!"
            echo "🌐 URL: http://127.0.0.1:5000"
            echo "📊 Debug mode: ON"
            echo "📝 Logs: $APP_DIR/flask_app.log"
            echo "🔧 PID: $(cat $PID_FILE)"
            echo "=================================="
            echo ""
            echo "To stop: ./stop_app.sh"
            return 0
        fi
        
        if [ $i -eq 1 ]; then
            log "Waiting for app to respond..."
        fi
        
        sleep 1
    done
    
    error "Health check failed - app not responding"
    cat "$APP_DIR/flask_app.log"
    exit 1
}

# Main execution
main() {
    log "==================== MPA App Startup ===================="
    
    check_running
    check_environment
    check_dependencies
    check_port
    start_app
    health_check
    
    log "Startup completed successfully"
}

# Run main function
main "$@"