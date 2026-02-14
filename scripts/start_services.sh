#!/bin/bash

###############################################################################
# OCR Microservice Orchestration Script
# Starts all services: Receiver, Sender, Debug UI
# Shows logs in real-time
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

# Activate virtual environment if it exists
if [ -d "venv/bin" ]; then
    echo -e "${CYAN}→ Activating virtual environment...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OCR Microservice Orchestration - Starting...        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo

###############################################################################
# Pre-flight Checks
###############################################################################

echo -e "${BLUE}[1/5] Pre-flight checks...${NC}"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}✗ Redis is not running!${NC}"
    echo -e "${YELLOW}  Please start Redis first:${NC}"
    echo -e "  ${CYAN}brew services start redis${NC} (macOS)"
    echo -e "  ${CYAN}sudo systemctl start redis${NC} (Linux)"
    exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Clear old logs
> logs/receiver.log
> logs/sender.log
> logs/debug_server.log

echo -e "${GREEN}✓ Logs directory ready${NC}"
echo

###############################################################################
# Install Dependencies
###############################################################################

echo -e "${BLUE}[2/5] Checking dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installing/updating Python dependencies...${NC}"
    python3 -m pip install -r requirements.txt > /dev/null 2>&1 || {
        echo -e "${YELLOW}⚠ Some dependencies may have failed. Continuing...${NC}"
    }
    echo -e "${GREEN}✓ Dependencies checked${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi
echo

###############################################################################
# Start Services
###############################################################################

echo -e "${BLUE}[3/5] Starting services...${NC}"

# Function to start a service
start_service() {
    local name=$1
    local script=$2
    local port=$3
    local pid_file=$4
    
    echo -e "${YELLOW}→ Starting ${name}...${NC}"
    
    # Check if already running
    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo -e "${YELLOW}  ${name} is already running (PID: $(cat $pid_file))${NC}"
        return
    fi
    
    # Start service in background
    nohup python3 "$script" > "logs/${name}.log" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait a bit and check if it's still running
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✓ ${name} started (PID: ${pid}, Port: ${port})${NC}"
    else
        echo -e "${RED}✗ ${name} failed to start${NC}"
        cat "logs/${name}.log"
        exit 1
    fi
}

# Start Receiver Service (FastAPI)
start_service "receiver" "src/receiver.py" "8001" "logs/receiver.pid"

# Start Sender Worker
start_service "sender" "src/sender.py" "N/A" "logs/sender.pid"

# Start Debug UI (Flask)
start_service "debug_server" "debug/server.py" "5000" "logs/debug_server.pid"

echo
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo

###############################################################################
# Service Information
###############################################################################

echo -e "${BLUE}[4/5] Service endpoints:${NC}"
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Service         │ Status  │ Port  │ Endpoint              ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Receiver API    │ ${GREEN}RUNNING${CYAN} │ 8001  │ http://localhost:8001  ║${NC}"
echo -e "${CYAN}║  Sender Worker   │ ${GREEN}RUNNING${CYAN} │  N/A  │ Background process     ║${NC}"
echo -e "${CYAN}║  Debug UI        │ ${GREEN}RUNNING${CYAN} │ 5000  │ http://localhost:5000  ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo

echo -e "${BLUE}📡 API Endpoints:${NC}"
echo -e "  ${CYAN}POST${NC}   http://localhost:8001/process         - Submit OCR job"
echo -e "  ${CYAN}GET${NC}    http://localhost:8001/result/{id}     - Query result"
echo -e "  ${CYAN}GET${NC}    http://localhost:8001/status          - Service health"
echo

echo -e "${BLUE}🌐 Web Interface:${NC}"
echo -e "  ${CYAN}→ Open in browser: ${GREEN}http://localhost:5000${NC}"
echo

###############################################################################
# Log Monitoring
###############################################################################

echo -e "${BLUE}[5/5] Monitoring logs...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services and exit${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo

# Trap Ctrl+C to stop all services
trap 'echo -e "\n${YELLOW}Stopping all services...${NC}"; bash scripts/stop_services.sh; exit' INT

# Tail all logs
tail -f logs/receiver.log logs/sender.log logs/debug_server.log 2>/dev/null | while read line; do
    if [[ "$line" == *"receiver"* ]]; then
        echo -e "${BLUE}[RECEIVER]${NC} $line"
    elif [[ "$line" == *"sender"* ]]; then
        echo -e "${GREEN}[SENDER]${NC} $line"
    elif [[ "$line" == *"debug"* ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $line"
    else
        echo "$line"
    fi
done
