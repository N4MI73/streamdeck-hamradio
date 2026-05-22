# ============================================================
#  PSTRotatorAz - Antenna Direction Control
#  Save to: C:\Ham Scripts\RotatorAzimuth.ps1
#
#  Sends a UDP azimuth command to PSTRotatorAz.
#  PSTRotatorAz must be running with UDP Control enabled.
#
#  Usage:
#    .\RotatorAzimuth.ps1 -az 0     (North)
#    .\RotatorAzimuth.ps1 -az 45    (Northeast)
#    .\RotatorAzimuth.ps1 -az 90    (East)
#    .\RotatorAzimuth.ps1 -az 135   (Southeast)
#    .\RotatorAzimuth.ps1 -az 180   (South)
#    .\RotatorAzimuth.ps1 -az 225   (Southwest)
#    .\RotatorAzimuth.ps1 -az 270   (West)
#    .\RotatorAzimuth.ps1 -az 315   (Northwest)
#
#  Stream Deck setup (Advanced Launcher, one button per direction):
#    Executable: powershell.exe
#    Arguments:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\RotatorAzimuth.ps1" -az 270
# ============================================================

param (
    [int]$az = -1
)

# ---- Settings ----------------------------------------------

$udpHost = "127.0.0.1"   # PSTRotatorAz is on the same PC
$udpPort = 12000          # Must match Communication > UDP Control Port in PSTRotatorAz

# ---- Direction labels for display --------------------------

$directions = @{
    0   = "NORTH"
    45  = "NORTHEAST"
    90  = "EAST"
    135 = "SOUTHEAST"
    180 = "SOUTH"
    225 = "SOUTHWEST"
    270 = "WEST"
    315 = "NORTHWEST"
}

# ---- Validate input ----------------------------------------

if ($az -lt 0 -or $az -gt 360) {
    Write-Host "ERROR: Please provide a valid azimuth between 0 and 360." -ForegroundColor Red
    Write-Host "Usage: .\RotatorAzimuth.ps1 -az 270" -ForegroundColor Yellow
    Start-Sleep -Seconds 4
    exit
}

# ---- Build PSTRotatorAz UDP command ------------------------
# Format: <PST><AZIMUTH>xxx</AZIMUTH></PST>

$command = "<PST><AZIMUTH>$az</AZIMUTH></PST>"

# ---- Send UDP packet ---------------------------------------

try {
    $udpClient = New-Object System.Net.Sockets.UdpClient
    $udpClient.Connect($udpHost, $udpPort)

    $bytes = [System.Text.Encoding]::ASCII.GetBytes($command)
    $udpClient.Send($bytes, $bytes.Length) | Out-Null
    $udpClient.Close()

    $label = if ($directions.ContainsKey($az)) { " ($($directions[$az]))" } else { "" }
    Write-Host "Rotator command sent: $az degrees$label" -ForegroundColor Green
    Write-Host "Command: $command" -ForegroundColor Cyan

} catch {
    Write-Host "ERROR: Could not send UDP command." -ForegroundColor Red
    Write-Host "Make sure PSTRotatorAz is running with UDP Control enabled." -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
    Start-Sleep -Seconds 4
    exit
}

Start-Sleep -Seconds 2
