# ============================================================
#  Ham Radio - Close All Apps
#  Save to: C:\Ham Scripts\CloseHamRadio.ps1
#
#  Cleanly closes all ham radio apps in the correct order.
#
#  Stream Deck setup (Advanced Launcher):
#    Executable: powershell.exe
#    Arguments:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\CloseHamRadio.ps1"
# ============================================================

Add-Type -AssemblyName PresentationFramework

function Show-Prompt($message, $title) {
    return [System.Windows.MessageBox]::Show(
        $message,
        $title,
        [System.Windows.MessageBoxButton]::YesNo,
        [System.Windows.MessageBoxImage]::Question
    )
}

function Show-Info($message, $title) {
    [System.Windows.MessageBox]::Show(
        $message,
        $title,
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Information
    ) | Out-Null
}

function Close-App($processName, $friendlyName) {
    $procs = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "Closing $friendlyName..." -ForegroundColor Yellow
        $procs | ForEach-Object { $_.CloseMainWindow() | Out-Null }
        Start-Sleep -Seconds 2
        # Force close if still running
        $remaining = Get-Process -Name $processName -ErrorAction SilentlyContinue
        if ($remaining) {
            $remaining | Stop-Process -Force
            Write-Host "  Force closed $friendlyName" -ForegroundColor Red
        } else {
            Write-Host "  $friendlyName closed OK" -ForegroundColor Green
        }
    } else {
        Write-Host "$friendlyName was not running" -ForegroundColor DarkGray
    }
}

# ── Step 1: Confirm shutdown ──────────────────────────────
$confirm = Show-Prompt "Close all ham radio apps?`n`nThis will close:`n  - JTAlert`n  - WSJT-X`n  - MRP40`n  - ACLog`n  - PSTRotatorAz`n  - Ham Radio Dashboard (Chrome)`n`nAre you ready to shut down?" "Ham Radio - Close All Apps"

if ($confirm -ne "Yes") {
    Write-Host "Shutdown cancelled." -ForegroundColor Cyan
    exit
}

# ── Step 2: PSTRotator warning ────────────────────────────
Show-Info "ROTATOR REMINDER:`n`nBefore closing PSTRotatorAz, please return`nthe rotator to NORTH (0 degrees).`n`nClick OK when the rotator is at 0 degrees." "Ham Radio - Rotator Check"

# ── Step 3: Close apps in correct order ──────────────────
Write-Host "`n=== Closing Ham Radio Apps ===" -ForegroundColor Magenta

# JTAlert first (depends on WSJT-X)
Close-App "JTAlertV2"  "JTAlert"

Start-Sleep -Seconds 1

# WSJT-X before ACLog
Close-App "wsjtx"      "WSJT-X"

Start-Sleep -Seconds 1

# MRP40 (CW decoder)
Close-App "MRP40v67"   "MRP40"

Start-Sleep -Seconds 1

# ACLog
Close-App "aclog"      "ACLog"

Start-Sleep -Seconds 1

# PSTRotatorAz
Close-App "PstRotatorAz" "PSTRotatorAz"

# ── Step 4: Close dashboard Chrome tab ───────────────────
Write-Host "Closing Ham Radio Dashboard..." -ForegroundColor Yellow
$chromeDash = Get-Process -Name "chrome" -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*N4MI*" -or $_.MainWindowTitle -like "*Propagation Dashboard*"
}
if ($chromeDash) {
    $chromeDash | ForEach-Object { $_.CloseMainWindow() | Out-Null }
    Write-Host "  Dashboard tab closed" -ForegroundColor Green
} else {
    Write-Host "  Dashboard tab not found (may already be closed)" -ForegroundColor DarkGray
}

# ── Step 5: Python server prompt ─────────────────────────
$pyProc = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*dashboard_server*" -or $_.Path -like "*python*"
}

# Fallback: check if anything is listening on port 8073
$portInUse = netstat -ano | Select-String ":8073 " | Select-String "LISTENING"

if ($portInUse) {
    $stopServer = Show-Prompt "The Ham Radio Dashboard server is still running on port 8073.`n`nStop the Python server?`n`n  Yes = Stop server (frees memory)`n  No  = Leave running (dashboard opens faster next time)" "Ham Radio - Python Server"

    if ($stopServer -eq "Yes") {
        # Find and stop the python process on port 8073
        $pidLine = netstat -ano | Select-String ":8073 " | Select-String "LISTENING"
        if ($pidLine) {
            $pid8073 = ($pidLine -split '\s+')[-1]
            try {
                Stop-Process -Id $pid8073 -Force -ErrorAction SilentlyContinue
                Write-Host "  Python server stopped (PID $pid8073)" -ForegroundColor Green
            } catch {
                Write-Host "  Could not stop server automatically. Close it manually in Task Manager." -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  Python server left running" -ForegroundColor Cyan
    }
} else {
    Write-Host "Python server was not running" -ForegroundColor DarkGray
}

# ── Done ─────────────────────────────────────────────────
Write-Host "`nAll done! 73!" -ForegroundColor Green
Start-Sleep -Seconds 3
