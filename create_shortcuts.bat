@echo off
REM ================================================================
REM  Mythos AI - Shortcut Creator
REM  Creates shortcuts WITHOUT console window
REM ================================================================
setlocal
set "MYTHOS_HOME=%~dp0"

echo.
echo  ========================================
echo   MYTHOS AI - Shortcut Creator
echo  ========================================
echo.

REM Find Python
set "PY="
for %%P in (python.exe pythonw.exe py.exe) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set "PY=%%P"
        goto :found
    )
)

REM Try Mythos venv
if exist "%MYTHOS_HOME%.mythos_venv\Scripts\pythonw.exe" (
    set "PY=%MYTHOS_HOME%.mythos_venv\Scripts\pythonw.exe"
    goto :found
)
if exist "%MYTHOS_HOME%.mythos_venv\Scripts\python.exe" (
    set "PY=%MYTHOS_HOME%.mythos_venv\Scripts\python.exe"
    goto :found
)

echo [Error] Python not found.
pause
exit /b 1

:found
echo Using: %PY%
echo.

"%PY%" "%MYTHOS_HOME%create_shortcuts.py"

echo.
pause
endlocal
