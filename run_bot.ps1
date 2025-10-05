# Step 1: Check if virtual environment exists
if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Step 2: Activate virtual environment
Write-Host "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

# Step 3: Install requirements if not installed
Write-Host "Installing required packages..."
pip install -r requirements.txt

# Step 4: Run the bot
Write-Host "Starting the bot..."
python bot.py

# Keep console open after exit
Pause
