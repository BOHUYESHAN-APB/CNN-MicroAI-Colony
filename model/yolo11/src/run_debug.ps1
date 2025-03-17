Write-Host "Running debug script..."
Write-Host "Current directory: $(Get-Location)"
Write-Host ""

# Activate virtual environment
& ../.venv/Scripts/Activate.ps1

# Run Python script with output
python -u debug_config.py *>&1 | Tee-Object -FilePath "debug_output.txt"

Write-Host ""
Write-Host "Debug output has been saved to debug_output.txt"
