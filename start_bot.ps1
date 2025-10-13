# StudyBot Auto-Start Script
Write-Host "Starting StudyBot setup..." -ForegroundColor Cyan

# Check if Python is installed
try {
    python --version
} catch {
    Write-Host "Python is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/"
    Exit 1
}

# Check if virtualenv is installed
$virtualenvInstalled = python -m pip list | Select-String -Pattern "^virtualenv"
if (-not $virtualenvInstalled) {
    Write-Host "Installing virtualenv..." -ForegroundColor Yellow
    python -m pip install virtualenv
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# Start the bot
Write-Host "Starting StudyBot..." -ForegroundColor Green
python bot.py