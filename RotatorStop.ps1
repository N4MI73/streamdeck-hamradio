# ============================================================
#  PSTRotatorAz - Stop Rotation
#  Save to: C:\Ham Scripts\RotatorStop.ps1
#
#  Immediately stops antenna rotation via UDP command.
#  PSTRotatorAz must be running with UDP Control enabled.
#
#  Stream Deck setup (Advanced Launcher):
#    Executable: powershell.exe
#    Arguments:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\RotatorStop.ps1"
# ============================================================

$udpHost = "127.0.0.1"
$udpPort = 12000

try {
    $command  = "<PST><STOP>1</STOP></PST>"
    $udpClient = New-Object System.Net.Sockets.UdpClient
    $udpClient.Connect($udpHost, $udpPort)
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($command)
    $udpClient.Send($bytes, $bytes.Length) | Out-Null
    $udpClient.Close()

    Write-Host "Rotation STOPPED." -ForegroundColor Red
    Write-Host "Command: $command" -ForegroundColor DarkGray

} catch {
    Write-Host "ERROR: Could not send stop command." -ForegroundColor Red
    Write-Host "Make sure PSTRotatorAz is running with UDP Control enabled." -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
    Start-Sleep -Seconds 4
    exit
}

Start-Sleep -Seconds 1
