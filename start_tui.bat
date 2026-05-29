@echo off
chcp 65001 >nul 2>&1
title TCM AI Health Advisor - TUI Mode

echo ============================================
echo    TCM AI Health Advisor - TUI Mode
echo ============================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

:: Get script directory
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"

:: Install deps if needed
if not exist "%BACKEND%\venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv "%BACKEND%\venv"
    call "%BACKEND%\venv\Scripts\activate.bat"
    echo [INFO] Installing backend dependencies...
    pip install -r "%BACKEND%\requirements.txt"
) else (
    call "%BACKEND%\venv\Scripts\activate.bat"
)

:: Check config
if not exist "%BACKEND%\data\config.json" (
    echo.
    echo [WARN] No config.json found.
    echo        Press S key in the app to configure API keys.
    echo.
    timeout /t 3 /nobreak >nul
)

echo [INFO] Launching TUI...
echo.
echo  Controls:
echo    S     - Open Settings
echo    Q     - Quit
echo    Ctrl+A - Start Analysis (in inquiry)
echo    R     - Restart (in result)
echo.

cd /d "%BACKEND%"
python run_tui.py
