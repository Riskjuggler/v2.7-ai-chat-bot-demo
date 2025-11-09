@echo off
REM Start Both Backend and Frontend for AI Chat Web Interface
REM This script starts both servers in separate windows

echo ========================================
echo   AI Chat Full Stack Server Startup
echo ========================================
echo.

REM Check if we're in the project root
if not exist "requirements.txt" (
    echo Error: Must run from project root directory
    echo Usage: scripts\start-all.bat
    exit /b 1
)

if not exist "frontend" (
    echo Error: frontend directory not found
    echo Must run from project root directory
    echo Usage: scripts\start-all.bat
    exit /b 1
)

REM Start backend in new window
echo Starting backend server in new window...
start "AI Chat Backend" cmd /k "scripts\start-backend.bat"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting frontend server in new window...
start "AI Chat Frontend" cmd /k "scripts\start-frontend.bat"

echo.
echo ========================================
echo   Servers are starting!
echo ========================================
echo.
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo Frontend:  http://localhost:3000
echo.
echo Each server is running in its own window.
echo Close the windows to stop the servers.
echo.

pause
