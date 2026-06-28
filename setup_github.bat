@echo off
REM ============================================================
REM  Mythos GitHub Setup - Push to GitHub
REM  This script helps you push Mythos to your GitHub account
REM ============================================================
setlocal

echo.
echo ========================================
echo   Mythos GitHub Setup
echo ========================================
echo.

REM Check if Git is installed
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git not found. Please install Git first:
    echo         https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/5] Checking Git configuration...
echo.

REM Check if user is configured
for /f "tokens=*" %%i in ('git config user.name') do set USERNAME=%%i
for /f "tokens=*" %%i in ('git config user.email') do set USEREMAIL=%%i

if "%USERNAME%"=="Mythos AI" (
    echo [!] Git user not configured. Let's set it up.
    echo.
    set /p GITNAME="Enter your name: "
    set /p GITEMAIL="Enter your email: "
    git config --global user.name "%GITNAME%"
    git config --global user.email "%GITEMAIL%"
    echo [OK] Git configured: %GITNAME% ^<%GITEMAIL%^>
) else (
    echo [OK] Git user: %USERNAME%
)

echo.
echo [2/5] Checking GitHub CLI...
echo.

REM Check if GitHub CLI is installed
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] GitHub CLI not found. Installing...
    echo     Download from: https://cli.github.com/
    echo.
    echo     Or install with winget:
    echo       winget install GitHub.cli
    echo.
    echo After installing, run this script again.
    pause
    exit /b 1
)

echo [OK] GitHub CLI found.

echo.
echo [3/5] Login to GitHub...
echo.

gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo Please login to GitHub:
    gh auth login --web -p https
) else (
    echo [OK] Already logged in to GitHub.
)

echo.
echo [4/5] Creating repository...
echo.

REM Get current directory
set "REPODIR=%~dp0"
cd /d "%REPODIR%"

REM Check if remote exists
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Remote already configured.
) else (
    echo Creating new repository on GitHub...
    gh repo create mythos --public --source=. --push --description "Mythos AI - Autonomous Agent with CLI and Desktop"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to create repository.
        echo         Make sure you're logged in and the repo name is available.
        pause
        exit /b 1
    )
)

echo.
echo [5/5] Pushing to GitHub...
echo.

git push -u origin master
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Push failed. Try:
    echo         git push -u origin master
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! Mythos is on GitHub
echo ========================================
echo.
echo   Repository: https://github.com/%USERNAME%/mythos
echo.
echo   To install on another computer:
    echo     git clone https://github.com/%USERNAME%/mythos.git
    echo     cd mythos
    echo     python install.py
echo.
echo ========================================
echo.

pause
