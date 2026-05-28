# StartHamShackFeedPro.ps1
# Launcher for HamShackFeed Pro
# Place in C:\Ham Scripts\ alongside your other ham scripts.

$scriptDir  = "C:\Ham Scripts\hamshackfeed_pro"
$serverScript = Join-Path $scriptDir "server.py"
$reqFile    = Join-Path $scriptDir "requirements.txt"
$port       = 8074

# ── Check Python ──────────────────────────────────────────
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    [System.Windows.Forms.MessageBox]::Show(
        "Python not found. Install Python 3.13 from the Microsoft Store or python.org and ensure it is on PATH.",
        "HamShackFeed Pro", "OK", "Error"
    )
    exit 1
}

# ── Install dependencies if needed ────────────────────────
$flask = python -c "import flask" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    python -m pip install -r $reqFile --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pip install failed. Run manually:" -ForegroundColor Red
        Write-Host "  pip install -r `"$reqFile`"" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Dependencies installed." -ForegroundColor Green
}

# ── Kill any existing instance on port 8074 ───────────────
$existing = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($existing) {
    $pid = ($existing | Select-Object -First 1).OwningProcess
    Write-Host "Stopping existing instance on port $port (PID $pid)..." -ForegroundColor Yellow
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# ── Launch server ─────────────────────────────────────────
Write-Host "Starting HamShackFeed Pro on port $port..." -ForegroundColor Cyan
Set-Location $scriptDir
Start-Process python -ArgumentList $serverScript -WindowStyle Minimized
