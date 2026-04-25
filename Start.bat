@echo off
setlocal enabledelayedexpansion
cd /d %~dp0
title File Uploader - Setup & Launch
color 0A

echo ============================================
echo   File Uploader - Requirement Checker
echo ============================================
echo.

:: 1. CHECK PYTHON
echo [1/4] Checking Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found. Please install it.
    pause
    exit /b 1
)

:: 2. CHECK pip
echo [2/4] Checking pip...
python -m pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installing pip...
    python -m ensurepip --upgrade
)

:: 3. CHECK PACKAGES
echo [3/4] Checking required packages...

python -c "import flask" >nul 2>&1 || set MISSING=1
python -c "import qrcode" >nul 2>&1 || set MISSING=1
python -c "from PIL import Image" >nul 2>&1 || set MISSING=1

IF "%MISSING%"=="1" (
    echo Installing required packages...
    python -m pip install flask "qrcode[pil]" Pillow
)

:: 4. START SERVER
echo [4/4] Starting server...
echo.

echo ============================================
echo   Server running on http://127.0.0.1:5000
echo ============================================
echo.

:: Run Python in same window
python Server.py

:: When Python exits
echo.
echo Server stopped. Cleaning up...

:: Kill only this cmd window's child python process
for /f "tokens=2 delims=," %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH') do (
    taskkill /PID %%~a /F >nul 2>&1
)

echo Done.
pause
exit