# ============================================================
#  Ham Radio Dashboard - Local Web Server Launcher
#  Save to: C:\Ham Scripts\StartDashboard.ps1
#
#  Stream Deck setup (Advanced Launcher):
#    Executable: powershell.exe
#    Arguments:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\StartDashboard.ps1"
# ============================================================

$dashboardFolder = "C:\Ham Scripts"
$dashboardFile   = "N4MI_PropagationDashboard.html"
$serverScript    = "C:\Ham Scripts\dashboard_server.py"
$port            = 8073
$chrome          = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profile         = "Profile 1"
$url             = "http://localhost:$port/$dashboardFile"

# Check if Python is available
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python") { $python = $cmd; break }
    } catch {}
}

if (-not $python) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "Python was not found on this computer.`n`nPlease install Python 3.13 from the Microsoft Store and try again.",
        "Dashboard Launcher - Python Required",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Warning
    ) | Out-Null
    exit
}

# Check if server is already running on port
$inUse = netstat -ano | Select-String ":$port " | Select-String "LISTENING"

if ($inUse) {
    Write-Host "Server already running on port $port - opening Chrome..." -ForegroundColor Green
} else {
    Write-Host "Starting Ham Radio Dashboard server..." -ForegroundColor Cyan

    Start-Process $python `
        -ArgumentList "`"$serverScript`"" `
        -WorkingDirectory $dashboardFolder `
        -WindowStyle Hidden

    Start-Sleep -Seconds 2
    Write-Host "Server started." -ForegroundColor Green
}

# Open dashboard in Chrome
Write-Host "Opening dashboard in Chrome..." -ForegroundColor Green
Start-Process $chrome -ArgumentList "--profile-directory=`"$profile`" $url"

Write-Host ""
Write-Host "Dashboard running at: $url" -ForegroundColor Cyan
Write-Host "73!" -ForegroundColor Green
Start-Sleep -Seconds 3
