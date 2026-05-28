$pidFile = "C:\Ham Scripts\dashboard.pid"

if (Test-Path $pidFile) {
    $targetPid = [int](Get-Content $pidFile)
    try {
        Stop-Process -Id $targetPid -Force -ErrorAction Stop
        Remove-Item $pidFile
        Write-Host "  Dashboard server stopped (PID $targetPid). 73!" -ForegroundColor Green
    } catch {
        Write-Host "  Process $targetPid not found — server may have already stopped." -ForegroundColor Yellow
        Remove-Item $pidFile
    }
} else {
    Write-Host "  No dashboard.pid found — server is not running." -ForegroundColor Yellow
}

Start-Sleep 2
