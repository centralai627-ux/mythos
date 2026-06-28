@echo off
REM ============================================================
REM  Manual GitHub Setup for Mythos
REM  Follow these steps to create repository manually
REM ============================================================
setlocal

echo.
echo ========================================
echo   Manual GitHub Setup
echo ========================================
echo.
echo   Follow these steps:
echo.
echo   1. Open browser and go to:
echo      https://github.com/new
echo.
echo   2. Fill in the form:
echo      - Repository name: mythos
echo      - Description: Mythos AI - Autonomous Agent
echo      - Select: Public
echo      - DON'T initialize with README
echo.
echo   3. Click: Create repository
echo.
echo   4. After creating, come back here and press any key
echo.
pause

echo.
echo [1/2] Setting up remote...
echo.

cd /d "%~dp0"
git remote remove origin 2>nul
git remote add origin https://github.com/centralai627-ux/mythos.git

echo [OK] Remote configured.
echo.
echo [2/2] Pushing to GitHub...
echo.

git push -u origin master

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Push failed.
    echo         Make sure you created the repository on GitHub.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! Mythos is on GitHub
echo ========================================
echo.
echo   Repository: https://github.com/centralai627-ux/mythos
echo.
echo   To install on another computer:
echo     git clone https://github.com/centralai627-ux/mythos.git
echo     cd mythos
echo     python install.py
echo.
echo ========================================
echo.

pause
