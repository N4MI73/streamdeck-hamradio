# StopManualShelf.ps1
$PidFile = "C:\Ham Scripts\manualshelf\manualshelf.pid"

if (Test-Path $PidFile) {
    $pid = Get-Content $PidFile
    try {
        Stop-Process -Id $pid -Force -ErrorAction Stop
        Write-Host "ManualShelf stopped (PID $pid)" -ForegroundColor Green
    } catch {
        Write-Host "Process $pid not found (already stopped)" -ForegroundColor Yellow
    }
    Remove-Item $PidFile -Force
} else {
    Write-Host "No PID file found — ManualShelf may not be running" -ForegroundColor Yellow
    # Fallback: kill any python process running server.py
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -like "*manualshelf*" -or $_.CommandLine -like "*server.py*"
    } | Stop-Process -Force
}
