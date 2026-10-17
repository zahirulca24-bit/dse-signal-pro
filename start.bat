@echo off
title DSE Signal Pro - Unified Terminal (Backend + Frontend)
color 0A
cd /d "%~dp0"

echo =====================================================================
echo           DSE SIGNAL PRO - 6-PILLAR DECISION ENGINE
echo             Unified Server (FastAPI Backend + Frontend)
echo =====================================================================
echo.

set "VENV_PY=Backend\.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    set "PYTHON_CMD=%VENV_PY%"
) else (
    set "PYTHON_CMD=python"
)

echo [*] Python Path: %PYTHON_CMD%
echo [*] Checking and freeing port 8080 (IPv4 and IPv6)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 4 } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>&1
echo [*] Starting Unified Server at http://localhost:8080 ...
echo [*] Frontend and Backend are running together in this terminal!
echo [*] Opening browser in 2 seconds...
echo.

:: Automatically launch browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8080"

:: Launch Unified FastAPI Server with hot-reload
"%PYTHON_CMD%" -m uvicorn main:app --app-dir Backend --host 127.0.0.1 --port 8080 --reload

:: Fallback to standalone server if uvicorn encounters any issue
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Notice: Switching to fallback standalone server (app/server.py)...
    "%PYTHON_CMD%" app/server.py
)

echo.
pause
