#!/bin/bash

# Start Backend Server for AI Chat Web Interface
# This script starts the FastAPI backend on port 8000

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  AI Chat Backend Server Startup${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/start-backend.sh${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your API keys${NC}"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Dependencies not installed. Installing...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}Dependencies installed${NC}"
    echo ""
fi

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: Port 8000 is already in use${NC}"
    echo -e "${YELLOW}To find the process using port 8000:${NC}"
    echo "  lsof -i :8000"
    echo ""
    echo -e "${YELLOW}To kill it:${NC}"
    echo "  kill \$(lsof -t -i:8000)"
    echo ""
    exit 1
fi

# Start the server
echo -e "${GREEN}Starting FastAPI backend server...${NC}"
echo -e "${YELLOW}Server will be available at: http://localhost:8000${NC}"
echo -e "${YELLOW}API docs available at: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Health check: http://localhost:8000/health${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
