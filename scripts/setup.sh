#!/bin/bash

###############################################################################
# OCR Microservice - Complete Setup Script
# Installs dependencies and prepares the environment
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OCR Microservice - Setup & Installation             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

###############################################################################
# 1. Check Python
###############################################################################

echo -e "${BLUE}[1/6] Checking Python...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo -e "${YELLOW}Please install Python 3.8 or higher${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
echo

###############################################################################
# 2. Check Redis
###############################################################################

echo -e "${BLUE}[2/6] Checking Redis...${NC}"

if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠ Redis is installed but not running${NC}"
        echo -e "${CYAN}Starting Redis...${NC}"
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start redis 2>/dev/null || {
                echo -e "${YELLOW}Please start Redis manually: brew services start redis${NC}"
            }
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl start redis 2>/dev/null || {
                echo -e "${YELLOW}Please start Redis manually: sudo systemctl start redis${NC}"
            }
        fi
    fi
else
    echo -e "${YELLOW}⚠ Redis is not installed${NC}"
    echo -e "${CYAN}Installation options:${NC}"
    echo
    echo -e "${CYAN}Option 1 - Native installation:${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "  brew install redis"
        echo -e "  brew services start redis"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "  sudo apt update"
        echo -e "  sudo apt install redis-server"
        echo -e "  sudo systemctl start redis"
    fi
    echo
    echo -e "${CYAN}Option 2 - Docker:${NC}"
    echo -e "  docker-compose up -d redis"
    echo
    read -p "Continue without Redis? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo

###############################################################################
# 3. Create directories
###############################################################################

echo -e "${BLUE}[3/6] Creating directories...${NC}"

mkdir -p logs
mkdir -p debug/static
mkdir -p debug/uploads

echo -e "${GREEN}✓ Directories created${NC}"
echo

###############################################################################
# 4. Install Python dependencies
###############################################################################

echo -e "${BLUE}[4/6] Installing Python dependencies...${NC}"
echo -e "${YELLOW}This may take a few minutes (PaddleOCR + dependencies)${NC}"
echo

# Upgrade pip first
python3 -m pip install --upgrade pip > /dev/null 2>&1

# Install requirements
if python3 -m pip install -r requirements.txt; then
    echo -e "${GREEN}✓ All dependencies installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Some dependencies may have failed${NC}"
    echo -e "${YELLOW}Try running manually: pip install -r requirements.txt${NC}"
fi
echo

###############################################################################
# 5. Test OCR model download
###############################################################################

echo -e "${BLUE}[5/6] Testing OCR model (first-time download)...${NC}"
echo -e "${YELLOW}This will download PaddleOCR models (~100MB)${NC}"

python3 -c "
import sys
try:
    from paddleocr import PaddleOCR
    print('Loading PaddleOCR model...')
    ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
    print('✓ OCR model loaded successfully')
except Exception as e:
    print(f'⚠ OCR model test failed: {e}', file=sys.stderr)
    print('This is OK - model will be downloaded on first use', file=sys.stderr)
" 2>&1 | while read line; do
    echo -e "${CYAN}  $line${NC}"
done

echo

###############################################################################
# 6. Final checks
###############################################################################

echo -e "${BLUE}[6/6] Final checks...${NC}"

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

# Check if all required files exist
REQUIRED_FILES=(
    "src/receiver.py"
    "src/sender.py"
    "src/queue_manager.py"
    "debug/server.py"
    "debug/index.html"
    "scripts/start_services.sh"
    "scripts/stop_services.sh"
)

ALL_GOOD=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing file: $file${NC}"
        ALL_GOOD=false
    fi
done

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All required files present${NC}"
else
    echo -e "${RED}✗ Some files are missing${NC}"
    exit 1
fi

echo

###############################################################################
# Done
###############################################################################

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ Setup Complete!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${CYAN}📚 Next steps:${NC}"
echo
echo -e "${YELLOW}1. Start all services:${NC}"
echo -e "   ${CYAN}bash scripts/start_services.sh${NC}"
echo
echo -e "${YELLOW}2. Open Debug UI in browser:${NC}"
echo -e "   ${CYAN}http://localhost:5000${NC}"
echo
echo -e "${YELLOW}3. Run test suite:${NC}"
echo -e "   ${CYAN}python3 scripts/test_services.py${NC}"
echo
echo -e "${YELLOW}4. Stop services:${NC}"
echo -e "   ${CYAN}bash scripts/stop_services.sh${NC}"
echo
echo -e "${BLUE}📖 Documentation:${NC}"
echo -e "   ${CYAN}cat MICROSERVICE_GUIDE.md${NC}"
echo
echo -e "${GREEN}Happy testing! 🚀${NC}"
