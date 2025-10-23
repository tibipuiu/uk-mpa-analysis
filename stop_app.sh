#!/bin/bash

# MPA Flask App Stop Script

APP_DIR="/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app"
PID_FILE="$APP_DIR/app.pid"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No PID file found. App may not be running.${NC}"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping MPA Flask App (PID: $PID)..."
    kill "$PID"
    
    # Wait for graceful shutdown
    sleep 2
    
    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Force stopping..."
        kill -9 "$PID"
    fi
    
    rm -f "$PID_FILE"
    echo -e "${GREEN}App stopped successfully${NC}"
else
    echo -e "${YELLOW}Process $PID not found. Cleaning up PID file.${NC}"
    rm -f "$PID_FILE"
fi