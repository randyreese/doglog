@echo off
echo -- Doglog Dev -----------------------------------------------
echo.
rem Kill any stale listeners on 8001 (e.g. orphaned reload-worker children from a
rem previous session) before starting a fresh server — prevents zombie processes
rem from load-balancing requests against stale code.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8001 " ^| findstr LISTENING') do taskkill /PID %%p /T /F >nul 2>&1

echo [1] Starting backend on http://127.0.0.1:8001 (new window)...
start "Doglog Backend (dev)" cmd /k "cd /d "%~dp0backend" && uvicorn main:app --reload --host 0.0.0.0 --port 8001"

echo [2] Starting mobile dev server...
cd /d "%~dp0mobile"
npm run dev
