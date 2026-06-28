@echo off
title Mythos Security Gateway
mode con cols=140 lines=45
color 0B

REM ============================================================
REM  Mythos Lock Screen - Auto-Start Launcher
REM  Layer 2 Security - Runs on Windows boot
REM ============================================================

set "MYTHOS_HOME=C:\Users\Admin\Pictures\Mythos"
set "PYTHON_EXE=C:\Users\Admin\Pictures\Mythos\.mythos_venv\Scripts\python.exe"

echo.
echo   ============================================
echo     MYTHOS SECURITY GATEWAY
echo   ============================================
echo.
echo   [Mythos] Starting Security Gateway...
echo.

cd /d "%MYTHOS_HOME%"
if errorlevel 1 (
    echo   [ERROR] Cannot access Mythos directory: %MYTHOS_HOME%
    echo.
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo   [ERROR] Python not found at: %PYTHON_EXE%
    echo   [Mythos] Searching for Python on PATH...
    for %%P in (python py python3) do (
        where %%P >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%%P"
            echo   [Mythos] Found: %%P
            goto :run_lock
        )
    )
    echo   [ERROR] No Python interpreter found!
    echo.
    pause
    exit /b 1
)

:run_lock
echo   [Mythos] Python: %PYTHON_EXE%
echo   [Mythos] Launching lock screen...
echo.

REM Run Python DIRECTLY in this window (no 'start' — keeps the window open).
"%PYTHON_EXE%" "%MYTHOS_HOME%\mythos.py" --lock

if errorlevel 1 (
    echo.
    echo   [ERROR] Mythos lock screen exited with error!
    echo   Python: %PYTHON_EXE%
    echo   Script: %MYTHOS_HOME%\mythos.py
    echo.
    pause
)
