<#
  shacklink.ps1  -  handler for n4mi-shack: links from DXMon Live (ham computer only)
  ---------------------------------------------------------------------------
  DXMon Live's Tune and Rotate buttons are plain links. Windows hands each link
  to this script, which checks it strictly and then calls the existing tools:

    n4mi-shack:tune?freq=14025000&mode=CW     ->  rig.ps1 tune 14025000 CW
    n4mi-shack:rotate?az=106                  ->  ..\RotatorAzimuth.ps1 -az 106

  Contract (agreed with DXMon 2026-11-02 / 2026-11-22): freq whole Hz digits,
  mode exactly CW or SSB, az whole degrees 0-359. Anything else is logged and
  ignored. Nothing here can transmit.

  Setup (Windows PowerShell 5.1, per user, no admin rights):
    powershell.exe -ExecutionPolicy Bypass -File "C:\Ham Scripts\rigcontrol\shacklink.ps1" -Install
    powershell.exe -ExecutionPolicy Bypass -File "C:\Ham Scripts\rigcontrol\shacklink.ps1" -Status
    powershell.exe -ExecutionPolicy Bypass -File "C:\Ham Scripts\rigcontrol\shacklink.ps1" -Uninstall

  Chrome opens these links without a prompt only from http://192.168.6.29:8083,
  via the AutoLaunchProtocolsFromOrigins policy (HKLM, set 2026-11-22).
  Log: shacklink.log in this folder (rig actions also log to rig.log).
#>
param(
    [Parameter(Position = 0)][string]$Url = '',
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Status
)

$Scheme  = 'n4mi-shack'
$KeyPath = "HKCU:\Software\Classes\$Scheme"
$LogFile = Join-Path $PSScriptRoot 'shacklink.log'
$Rig     = Join-Path $PSScriptRoot 'rig.ps1'
$Rotator = Join-Path (Split-Path $PSScriptRoot -Parent) 'RotatorAzimuth.ps1'

function Write-LinkLog([string]$msg) {
    $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Write-Output $line
    try {
        if ((Test-Path $LogFile) -and (Get-Item $LogFile).Length -gt 200KB) {
            Move-Item $LogFile "$LogFile.old" -Force
        }
        Add-Content -Path $LogFile -Value $line
    } catch { }
}

# ---------------- registration ----------------
if ($Install) {
    $ps   = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $con  = Join-Path $env:SystemRoot 'System32\conhost.exe'
    # conhost --headless: no console window flashes on each click.
    # -File (not -Command): the link is passed as plain text, never run as code.
    $cmd = '"{0}" --headless "{1}" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{2}" "%1"' -f $con, $ps, $PSCommandPath
    New-Item -Path $KeyPath -Force | Out-Null
    Set-Item -Path $KeyPath -Value 'URL:N4MI Shack Link'
    New-ItemProperty -Path $KeyPath -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null
    New-Item -Path "$KeyPath\shell\open\command" -Force | Out-Null
    Set-Item -Path "$KeyPath\shell\open\command" -Value $cmd
    Write-Output "Registered $Scheme`: for $env:USERNAME"
    Write-Output "Command: $cmd"
    exit 0
}
if ($Uninstall) {
    if (Test-Path $KeyPath) { Remove-Item -Path $KeyPath -Recurse -Force; Write-Output "Removed $Scheme`: registration" }
    else { Write-Output "$Scheme`: was not registered" }
    exit 0
}
if ($Status -or -not $Url) {
    if (Test-Path "$KeyPath\shell\open\command") {
        Write-Output ("Registered: " + (Get-Item "$KeyPath\shell\open\command").GetValue(''))
    } else { Write-Output "$Scheme`: is not registered for $env:USERNAME" }
    Write-Output "Log: $LogFile"
    exit 0
}

# ---------------- handle one link ----------------
$shown = ($Url -replace '[\x00-\x1F\x7F]', '?')
if ($shown.Length -gt 300) { $shown = $shown.Substring(0, 300) + '...' }

function Reject([string]$why) { Write-LinkLog "REJECTED ($why): $shown"; exit 2 }

# Whole link: scheme, action, then only letters/digits/=/& (an optional trailing / is tolerated)
$m = [regex]::Match($Url, '^n4mi-shack:(tune|rotate)\?([A-Za-z0-9=&]{1,100})/?$')
if (-not $m.Success) { Reject 'not a tune or rotate link' }
$action = $m.Groups[1].Value
$q = @{}
foreach ($pair in $m.Groups[2].Value.Split('&')) {
    $kv = $pair.Split('=')
    if ($kv.Count -ne 2 -or $kv[0] -eq '' -or $q.ContainsKey($kv[0])) { Reject 'bad parameters' }
    $q[$kv[0]] = $kv[1]
}

switch ($action) {
    'tune' {
        if ($q.Count -ne 2 -or -not $q.ContainsKey('freq') -or -not $q.ContainsKey('mode')) { Reject 'tune needs exactly freq and mode' }
        if ($q['freq'] -notmatch '^\d{1,9}$') { Reject 'freq must be whole Hz' }
        if ($q['mode'] -cnotmatch '^(CW|SSB)$') { Reject 'mode must be CW or SSB' }
        Write-LinkLog ("tune {0} {1}" -f $q['freq'], $q['mode'])
        $global:LASTEXITCODE = 0
        $out = & $Rig tune $q['freq'] $q['mode'] 2>&1
        $code = $LASTEXITCODE
        if ($code -eq 0) { Write-LinkLog '  -> OK' }
        else { Write-LinkLog "  -> FAILED (exit $code; details in rig.log): $(@($out)[-1])" }
        exit $code
    }
    'rotate' {
        if ($q.Count -ne 1 -or -not $q.ContainsKey('az')) { Reject 'rotate needs exactly az' }
        if ($q['az'] -notmatch '^\d{1,3}$' -or [int]$q['az'] -gt 359) { Reject 'az must be 0-359' }
        if (-not (Test-Path $Rotator)) { Write-LinkLog "  -> FAILED: $Rotator not found"; exit 1 }
        Write-LinkLog ("rotate {0}" -f $q['az'])
        & $Rotator -az ([int]$q['az']) *> $null
        Write-LinkLog '  -> sent to PSTRotatorAz'
        exit 0
    }
}
