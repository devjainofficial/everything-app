@echo off
cd /d "%~dp0"

echo ========================================
echo  Everything App - Starting all services
echo ========================================

:: 1. Ollama (local LLM server)
echo [1/4] Starting Ollama...
start "Ollama" cmd /c "ollama serve"

:: Wait for Ollama to be ready
timeout /t 5 /nobreak >nul

:: 2. LiteLLM Gateway (port 4000) - via start-gateway.ps1, which loads .env (Azure vars)
echo [2/4] Starting Gateway...
start "LiteLLM Gateway" powershell -ExecutionPolicy Bypass -File "%~dp0gateway\start-gateway.ps1"

:: Wait for gateway
timeout /t 8 /nobreak >nul

:: 3. FastAPI Backend (port 8000)
echo [3/4] Starting Backend...
start "FastAPI Backend" cmd /c ^
  ".venv\Scripts\uvicorn.exe backend.main:app --reload --port 8000"

:: 4. Next.js Frontend (port 3000)
echo [4/4] Starting Frontend...
start "Next.js Frontend" cmd /c "cd /d frontend && npm.cmd run dev"

echo.
echo All services launched in separate windows.
echo   Gateway  : http://localhost:4000
echo   Backend  : http://localhost:8000
echo   Frontend : http://localhost:3000
echo.
echo Press any key to open the frontend in your browser...
pause >nul
start http://localhost:3000
