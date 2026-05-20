@echo off
echo -- Deploy to Prod ------------------------------------------
echo.

echo [1/3] git pull on Mint...
ssh mini@mint.local "cd ~/doglog && git pull"
if %errorlevel% neq 0 (
    echo.
    echo Deploy failed at: git pull
    pause
    exit /b 1
)

echo.
echo [2/3] docker compose up -d --build...
ssh mini@mint.local "cd ~/doglog && docker compose up -d --build"
if %errorlevel% neq 0 (
    echo.
    echo Deploy failed at: docker compose up
    pause
    exit /b 1
)

echo.
echo [3/3] Note: if this is first deploy, add /doglog nginx location to mint.local
echo       See nginx/doglog-location.conf for the block to add to grow.conf
echo       Then: ssh mini@mint.local "sudo nginx -t ^&^& sudo systemctl reload nginx"

echo.
echo -- Deploy complete -----------------------------------------
pause
