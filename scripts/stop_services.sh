#!/bin/bash

###############################################################################
# OCR Microservice Stop Script
# Gracefully stops all running services
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OCR Microservice - Stopping Services...             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}→ Stopping ${name} (PID: ${pid})...${NC}"
            kill $pid 2>/dev/null || true
            
            # Wait for process to stop (max 5 seconds)
            local count=0
            while kill -0 $pid 2>/dev/null && [ $count -lt 10 ]; do
                sleep 0.5
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}  Force stopping ${name}...${NC}"
                kill -9 $pid 2>/dev/null || true
            fi
            
            echo -e "${GREEN}✓ ${name} stopped${NC}"
        else
            echo -e "${YELLOW}⚠ ${name} is not running${NC}"
        fi
        
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠ ${name} PID file not found${NC}"
    fi
}

# Stop all services
stop_service "Receiver Service" "logs/receiver.pid"
stop_service "Sender Worker" "logs/sender.pid"
stop_service "Debug Server" "logs/debug_server.pid"

echo
echo -e "${GREEN}✓ All services stopped${NC}"

# Optional: Show log file locations
echo
echo -e "${BLUE}📋 Log files preserved at:${NC}"
echo -e "  ${CYAN}logs/receiver.log${NC}"
echo -e "  ${CYAN}logs/sender.log${NC}"
echo -e "  ${CYAN}logs/debug_server.log${NC}"
echo

# Optional: Clean up old logs (commented out by default)
# echo -e "${YELLOW}Do you want to clean up log files? (y/N)${NC}"
# read -r response
# if [[ "$response" =~ ^[Yy]$ ]]; then
#     rm -f logs/*.log
#     echo -e "${GREEN}✓ Log files cleaned${NC}"
# fi

echo -e "${GREEN}Done!${NC}"
