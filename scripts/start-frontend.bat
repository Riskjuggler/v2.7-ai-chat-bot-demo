@echo off
REM Start Frontend Dev Server for AI Chat Web Interface
REM This script starts the React frontend on port 3000

echo =====================================
echo   AI Chat Frontend Server Startup
echo =====================================
echo.

REM Check if we're in the project root
if not exist "frontend" (
    echo Error: frontend directory not found
    echo Must run from project root directory
    echo Usage: scripts\start-frontend.bat
    exit /b 1
)

REM Navigate to frontend directory
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Node modules not found. Installing...
    call npm install
    echo Dependencies installed
    echo.
)

REM Check if port 3000 is available
netstat -ano | findstr ":3000" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo Error: Port 3000 is already in use
    echo To find the process using port 3000:
    echo   netstat -ano ^| findstr :3000
    echo.
    exit /b 1
)

REM Start the dev server
echo Starting React frontend dev server...
echo Server will be available at: http://localhost:3000
echo Make sure backend is running at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Vite
call npm run dev
