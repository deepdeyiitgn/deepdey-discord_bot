# Smoke test for StudyBot local services
# Run from repository root in PowerShell

# 1) Start the bot in one terminal:
#    .\.venv\Scripts\Activate.ps1; python bot.py

# 2) In another terminal, run these tests (set your API token in $env:API_TOKEN)
$env:API_TOKEN = 'your_api_token_here'
Write-Host "Testing /stats"
Invoke-RestMethod -Uri 'http://127.0.0.1:8080/stats' -Method GET | ConvertTo-Json
Write-Host "Testing /api/active_focus (requires token)"
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/active_focus?token=$env:API_TOKEN" -Method GET | ConvertTo-Json
Write-Host "Testing /api/leaderboard for guild 0 (requires token)"
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/leaderboard/0?token=$env:API_TOKEN" -Method GET | ConvertTo-Json
Write-Host "Testing /api/analytics (requires token)"
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/analytics?token=$env:API_TOKEN" -Method GET | ConvertTo-Json

Write-Host 'Smoke test complete'
