# StartManualShelf.ps1
# Launches ManualShelf on port 8075
# Place in C:\Ham Scripts\ or run from the manualshelf folder

$ScriptDir = "C:\Ham Scripts\manualshelf"
$Python    = "python"

Write-Host "Starting ManualShelf on http://localhost:8075" -ForegroundColor Cyan

Set-Location $ScriptDir

# Start the Flask server
$proc = Start-Process -FilePath $Python `
    -ArgumentList "server.py" `
    -WorkingDirectory $ScriptDir `
    -PassThru `
    -WindowStyle Minimized

# Save PID for stop script
$proc.Id | Out-File "$ScriptDir\manualshelf.pid" -Encoding ascii

Write-Host "ManualShelf running (PID $($proc.Id))" -ForegroundColor Green

# Wait a moment then open browser
Start-Sleep -Seconds 2
Start-Process "http://localhost:8075"
