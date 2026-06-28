@echo off
REM ============================================================
REM  Mythos AI v1.0.0 — Glasswing Edition
REM  Launches the Mythos CLI from any directory.
REM  Capabilities: code, shell, web, PDF, vision
REM ============================================================
setlocal
set "MYTHOS_HOME=%~dp0"
cd /d "%MYTHOS_HOME%"

REM Pick best available Python.
set "PY="
for %%P in (python py python3) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set "PY=%%P"
        goto :found
    )
)
:found
if "%PY%"=="" (
    echo [Mythos] Python not found. Install Python 3.9+ and retry.
    exit /b 1
)

REM Pass through all arguments.
"%PY%" "%MYTHOS_HOME%mythos.py" %*
endlocal
