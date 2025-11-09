@echo off
REM Start Backend Server for AI Chat Web Interface
REM This script starts the FastAPI backend on port 8000

echo =====================================
echo   AI Chat Backend Server Startup
echo =====================================
echo.

REM Check if we're in the project root
if not exist "requirements.txt" (
    echo Error: Must run from project root directory
    echo Usage: scripts\start-backend.bat
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env with your API keys
    echo.
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Dependencies not installed. Installing...
    pip install -r requirements.txt
    echo Dependencies installed
    echo.
)

REM Check if port 8000 is available
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo Error: Port 8000 is already in use
    echo To find the process using port 8000:
    echo   netstat -ano ^| findstr :8000
    echo.
    exit /b 1
)

REM Start the server
echo Starting FastAPI backend server...
echo Server will be available at: http://localhost:8000
echo API docs available at: http://localhost:8000/docs
echo Health check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
