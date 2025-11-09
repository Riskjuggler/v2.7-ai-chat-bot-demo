#!/bin/bash

# Start Both Backend and Frontend for AI Chat Web Interface
# This script starts both servers concurrently

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AI Chat Full Stack Server Startup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if we're in the project root
if [ ! -f "requirements.txt" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/start-all.sh${NC}"
    exit 1
fi

# Make scripts executable
chmod +x scripts/start-backend.sh scripts/start-frontend.sh

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servers stopped${NC}"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Start backend in background
echo -e "${GREEN}Starting backend server...${NC}"
./scripts/start-backend.sh > /tmp/ai-chat-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Backend failed to start. Check /tmp/ai-chat-backend.log${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo -e "${GREEN}Starting frontend server...${NC}"
cd frontend && npm run dev > /tmp/ai-chat-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo -e "${YELLOW}Waiting for frontend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}Frontend may still be starting...${NC}"
        break
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All servers are running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Backend:${NC}   http://localhost:8000"
echo -e "${YELLOW}API Docs:${NC}  http://localhost:8000/docs"
echo -e "${YELLOW}Frontend:${NC}  http://localhost:3000"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f /tmp/ai-chat-backend.log"
echo -e "  Frontend: tail -f /tmp/ai-chat-frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for user to press Ctrl+C
wait
