@echo off
REM ============================================================
REM  Create GitHub Repository for Mythos
REM  Run this script to create the repository on GitHub
REM ============================================================
setlocal

echo.
echo ========================================
echo   Create GitHub Repository
echo ========================================
echo.

REM Check if GitHub CLI is installed
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] GitHub CLI not found.
    echo.
    echo     Option 1: Install GitHub CLI
    echo     ========================================
    echo     Download: https://cli.github.com/
    echo     Or run: winget install GitHub.cli
    echo.
    echo     Option 2: Create manually
    echo     ========================================
    echo     1. Go to https://github.com/new
    echo     2. Repository name: mythos
    echo     3. Description: Mythos AI - Autonomous Agent
    echo     4. Select: Public
    echo     5. Click: Create repository
    echo     6. Then run this script again
    echo.
    pause
    exit /b 1
)

echo [1/3] Login to GitHub...
echo.

gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    gh auth login --web -p https
) else (
    echo [OK] Already logged in.
)

echo.
echo [2/3] Creating repository...
echo.

gh repo create mythos --public --source=. --push --description "Mythos AI - Autonomous Agent with CLI and Desktop"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to create repository.
    echo         Make sure you're logged in and the repo name is available.
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo ========================================
echo   Repository created successfully!
echo ========================================
echo.
echo   URL: https://github.com/centralai627-ux/mythos
echo.
echo   To install on another computer:
echo     git clone https://github.com/centralai627-ux/mythos.git
echo     cd mythos
echo     python install.py
echo.
echo ========================================
echo.

pause
