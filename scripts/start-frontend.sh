#!/bin/bash

# Start Frontend Dev Server for AI Chat Web Interface
# This script starts the React frontend on port 3000

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  AI Chat Frontend Server Startup${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Check if we're in the project root
if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: frontend directory not found${NC}"
    echo -e "${YELLOW}Must run from project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/start-frontend.sh${NC}"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Node modules not found. Installing...${NC}"
    npm install
    echo -e "${GREEN}Dependencies installed${NC}"
    echo ""
fi

# Check if port 3000 is available
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: Port 3000 is already in use${NC}"
    echo -e "${YELLOW}To find the process using port 3000:${NC}"
    echo "  lsof -i :3000"
    echo ""
    echo -e "${YELLOW}To kill it:${NC}"
    echo "  kill \$(lsof -t -i:3000)"
    echo ""
    exit 1
fi

# Start the dev server
echo -e "${GREEN}Starting React frontend dev server...${NC}"
echo -e "${YELLOW}Server will be available at: http://localhost:3000${NC}"
echo -e "${YELLOW}Make sure backend is running at: http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start Vite
npm run dev
