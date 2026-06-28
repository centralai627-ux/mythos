# Create GitHub Repository for Mythos
# Run this script in PowerShell

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Create GitHub Repository" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "[!] GitHub CLI not found." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install GitHub CLI:" -ForegroundColor Yellow
    Write-Host "  1. Download: https://cli.github.com/" -ForegroundColor White
    Write-Host "  2. Or run: winget install GitHub.cli" -ForegroundColor White
    Write-Host ""
    Write-Host "After installing, run this script again." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[1/3] Login to GitHub..." -ForegroundColor Green
Write-Host ""

# Check if already logged in
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    gh auth login --web -p https
} else {
    Write-Host "[OK] Already logged in." -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] Creating repository..." -ForegroundColor Green
Write-Host ""

# Create repository
gh repo create mythos --public --source=. --push --description "Mythos AI - Autonomous Agent with CLI and Desktop"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to create repository." -ForegroundColor Red
    Write-Host "Make sure you're logged in and the repo name is available." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host ""
Write-Host "[3/3] Done!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Repository created successfully!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL: https://github.com/centralai627-ux/mythos" -ForegroundColor White
Write-Host ""
Write-Host "To install on another computer:" -ForegroundColor Yellow
Write-Host "  git clone https://github.com/centralai627-ux/mythos.git" -ForegroundColor White
Write-Host "  cd mythos" -ForegroundColor White
Write-Host "  python install.py" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

pause
