# ============================================================
#  Ham Radio App Launcher
#  Save location: C:\Ham Scripts\HamRadioLauncher.ps1
#
#  IMPORTANT: Always right-click this script and choose
#  "Run as Administrator" so MRP40 launches correctly.
#
#  Usage from Stream Deck (System > Open, app = powershell.exe):
#    Arguments for FT8:   -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ft8
#    Arguments for CW:    -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode cw
#    Arguments for SSB:   -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ssb
# ============================================================

param (
    [string]$mode = "ft8"
)

# ---- APP PATHS ---------------------------------------------

$aclog       = "C:\Program Files (x86)\N3FJP Software - Affirmatech\Amateur Contact Log\aclog.exe"
$wsjtx       = "C:\WSJT\wsjtx\bin\wsjtx.exe"
$jtalert     = "C:\Program Files (x86)\HamApps\JTAlertV2\JTAlertV2.exe"
$mrp40       = "C:\Program Files (x86)\HamRadioSoftware\MRP40 Morse Decoder V67\MRP40v67.exe"
$pstrotator  = "C:\Program Files (x86)\PstRotatorAz\PstRotatorAz.exe"

# ---- DELAY SETTINGS (in seconds) ---------------------------

$shortDelay   = 3
$jtalertDelay = 4

# ---- HELPER FUNCTIONS --------------------------------------

function Launch($path, $name, $asAdmin = $false, $arguments = "", $workingDir = "") {
    if (Test-Path $path) {
        Write-Host "Launching $name..." -ForegroundColor Green
        $params = @{}
        if ($asAdmin)     { $params['Verb']         = 'RunAs' }
        if ($arguments)   { $params['ArgumentList'] = $arguments }
        if ($workingDir)  { $params['WorkingDirectory'] = $workingDir }
        Start-Process $path @params
    } else {
        Write-Host "WARNING: Could not find $name at:" -ForegroundColor Yellow
        Write-Host "  $path" -ForegroundColor Yellow
        Write-Host "  Check the path in the script and try again." -ForegroundColor Yellow
    }
}

function Pause-Seconds($seconds, $reason) {
    Write-Host "Waiting $seconds seconds $reason..." -ForegroundColor Cyan
    Start-Sleep -Seconds $seconds
}

function Show-Reminder($message) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        $message,
        "Ham Radio Launcher - Action Required",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Warning
    ) | Out-Null
}

# ============================================================
#  MODE LAUNCHER
# ============================================================

switch ($mode.ToLower()) {

    # --- FT8 / FT4 ------------------------------------------
    "ft8" {
        Write-Host "`n=== FT8 / FT4 Mode ===" -ForegroundColor Magenta

        Show-Reminder "FT8 / FT4 Mode:`n`nBefore continuing, make sure ACLog is configured for FT8:`n`n  - Rig Interface (COM 6):  OFF`n  - TCP API Server:         ON`n`nClick OK when ready to launch."

        Launch $aclog      "ACLog"
        Pause-Seconds $shortDelay "for ACLog to load"
        Launch $pstrotator "PSTRotatorAz"
        Pause-Seconds $shortDelay "for PSTRotatorAz to load"
        Launch $wsjtx      "WSJT-X"
        Pause-Seconds $jtalertDelay "for WSJT-X to load"
        Launch $jtalert    "JTAlert" $false "/wsjtx"
    }

    # --- CW -------------------------------------------------
    "cw" {
        Write-Host "`n=== CW Mode ===" -ForegroundColor Magenta

        Show-Reminder "CW Mode:`n`nBefore continuing, make sure ACLog is configured for CW/SSB:`n`n  - Rig Interface (COM 6):  ON`n  - TCP API Server:         OFF`n`nAfter MRP40 opens, verify these settings in MRP40:`n`n  - WinKeyer USB COM Port:  COM 10`n  - Sound Card:             2 - USB Audio CODEC`n`nClick OK when ready to launch."

        Launch $aclog      "ACLog"
        Pause-Seconds $shortDelay "for ACLog to load"
        Launch $pstrotator "PSTRotatorAz"
        Pause-Seconds $shortDelay "for PSTRotatorAz to load"
        Launch $mrp40      "MRP40" $true "" "C:\Program Files (x86)\HamRadioSoftware\MRP40 Morse Decoder V67"
    }

    # --- SSB ------------------------------------------------
    "ssb" {
        Write-Host "`n=== SSB Mode ===" -ForegroundColor Magenta

        Show-Reminder "SSB Mode:`n`nBefore continuing, make sure ACLog is configured for CW/SSB:`n`n  - Rig Interface (COM 6):  ON`n  - TCP API Server:         OFF`n`nClick OK when ready to launch."

        Launch $aclog      "ACLog"
        Pause-Seconds $shortDelay "for ACLog to load"
        Launch $pstrotator "PSTRotatorAz"
        Pause-Seconds $shortDelay "for PSTRotatorAz to load"
    }

    # --- Unknown mode ---------------------------------------
    default {
        Write-Host "Unknown mode: $mode" -ForegroundColor Red
        Write-Host "Available modes: ft8, cw, ssb" -ForegroundColor White
    }
}

Write-Host "`nAll apps launched! Good luck and 73!" -ForegroundColor Green
Start-Sleep -Seconds 3
