@echo off
chcp 65001 >nul 2>&1
title TCM AI Health Advisor

python "%~dp0launcher.py"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start. Please check the error above.
    pause
)
