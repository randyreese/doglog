@echo off
echo -- Doglog Dev -----------------------------------------------
echo.
echo [1] Starting backend on http://127.0.0.1:8001 (new window)...
start "Doglog Backend (dev)" cmd /k "cd /d "%~dp0backend" && uvicorn main:app --reload --host 127.0.0.1 --port 8001"

echo [2] Starting mobile dev server...
cd /d "%~dp0mobile"
npm run dev
