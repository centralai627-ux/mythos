@echo off
REM ================================================================
REM  Mythos AI - Icon Generator
REM  Generates modern Mythos logo icons
REM ================================================================
setlocal
set "MYTHOS_HOME=%~dp0"

echo.
echo  ========================================
echo   MYTHOS AI - Icon Generator
echo  ========================================
echo.

REM Find Python
set "PY="
for %%P in (python py python3) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set "PY=%%P"
        goto :found
    )
)

REM Try Mythos venv
if exist "%MYTHOS_HOME%.mythos_venv\Scripts\python.exe" (
    set "PY=%MYTHOS_HOME%.mythos_venv\Scripts\python.exe"
    goto :found
)

echo [Error] Python not found.
pause
exit /b 1

:found
echo Using Python: %PY%
echo.

"%PY%" "%MYTHOS_HOME%create_icon.py"

echo.
echo Press any key to exit...
pause >nul
endlocal
