<#
  rig.ps1  -  IC-7610 band / mode / filter control for the N4MI Stream Deck
  ---------------------------------------------------------------------------
  Talks to the radio over its LAN port (192.168.4.33) through a local
  "helper": rigplane's rigctld-compatible server, listening only on
  127.0.0.1:4532. COM6 is never touched, so N3FJP / WSJT-X keep the USB port.

  Usage (from a Stream Deck "Open" action or a PowerShell prompt):
    rig.ps1 band 20        save current spot to the band being left, recall 20 m
    rig.ps1 mode SSB       LSB below 10 MHz, USB above (60 m USB), FIL2, data off
    rig.ps1 mode USB|LSB   force USB or LSB, FIL2, data off
    rig.ps1 mode CW        CW   FIL3
    rig.ps1 mode DATA      USB-D1 FIL1
    rig.ps1 filter         step FIL1 -> FIL2 -> FIL3 -> FIL1 (keeps mode/data)
    rig.ps1 up | down      +/-100 kHz, stops at the US band edge (keeps mode)
    rig.ps1 split SSB      split ON, transmit 5 kHz above the MAIN frequency (SUB = TX)
    rig.ps1 split CW       split ON, transmit 1 kHz above
    rig.ps1 split OFF      split OFF
    rig.ps1 preamp         step preamp OFF -> P.AMP1 -> P.AMP2 -> OFF
    rig.ps1 nr | nb        toggle noise reduction / noise blanker
    rig.ps1 power OFF      radio off (standby or full shutdown, per the radio's Network
                           > Power OFF Setting); power ON is done at the radio
    rig.ps1 status         show helper state and what the radio is on
    rig.ps1 stop           stop the helper (releases the radio's LAN session)
    rig.ps1 setup          one-time: save radio network user/password (encrypted)

  Notes
  - Every action starts the helper if it is not running, and restarts it if it
    has stopped answering (first press after a reboot takes ~5-10 s).
  - Mode/filter use CI-V commands 06 and 1A 06, not 26: rigplane 2.11.1 waits
    for a data reply to a "26" write that the radio never sends (2 s stall).
  - Commands act on the radio's selected band (normally MAIN).
  - Band, mode and +/-100 kHz buttons turn split OFF first, so the transmit
    (SUB) frequency can never be left on another band or in another mode.
  - Windows PowerShell 5.1 compatible.
#>
param(
    [Parameter(Position = 0)][string]$Action = 'status',
    [Parameter(Position = 1)][string]$Arg = ''
)

# ---------------- configuration ----------------
$RadioIP   = '192.168.4.33'
$Port      = 4532
$Root      = $PSScriptRoot
$Exe       = Join-Path $Root 'venv\Scripts\rigplane.exe'
$CredFile  = Join-Path $Root 'rig_cred.xml'
$LogFile   = Join-Path $Root 'rig.log'
$Civ       = 'FE FE 98 E0'          # preamble, IC-7610 address 98h, controller E0h

# Band-stacking band codes and ranges, from the IC-7610 CI-V Reference Guide
# Band-stacking codes (BCD: 6 m is 0x10, not 0x0A) and register ranges (IC-7610 CI-V Reference Guide), plus
# US amateur band edges (Lo2/Hi2) used to stop the +/- step at the band edge.
$Bands = [ordered]@{
    '160' = @{ Code = 1;  Lo = 1800000;  Hi = 1999999;  Lo2 = 1800000;  Hi2 = 2000000  }
    '80'  = @{ Code = 2;  Lo = 3400000;  Hi = 4099999;  Lo2 = 3500000;  Hi2 = 4000000  }
    '40'  = @{ Code = 3;  Lo = 6900000;  Hi = 7499999;  Lo2 = 7000000;  Hi2 = 7300000  }
    '30'  = @{ Code = 4;  Lo = 9900000;  Hi = 10499999; Lo2 = 10100000; Hi2 = 10150000 }
    '20'  = @{ Code = 5;  Lo = 13900000; Hi = 14499999; Lo2 = 14000000; Hi2 = 14350000 }
    '17'  = @{ Code = 6;  Lo = 17900000; Hi = 18499999; Lo2 = 18068000; Hi2 = 18168000 }
    '15'  = @{ Code = 7;  Lo = 20900000; Hi = 21499999; Lo2 = 21000000; Hi2 = 21450000 }
    '12'  = @{ Code = 8;  Lo = 24400000; Hi = 25099999; Lo2 = 24890000; Hi2 = 24990000 }
    '10'  = @{ Code = 9;  Lo = 28000000; Hi = 29999999; Lo2 = 28000000; Hi2 = 29700000 }
    '6'   = @{ Code = 0x10; Lo = 50000000; Hi = 54000000; Lo2 = 50000000; Hi2 = 54000000 }
}
$StepHz = 100000      # up/down step
$DataCapable = @(0, 1, 2, 5)          # LSB, USB, AM, FM can carry a DATA mode
$ModeNames   = @{ 0='LSB'; 1='USB'; 2='AM'; 3='CW'; 4='RTTY'; 5='FM'; 7='CW-R'; 8='RTTY-R' }

# ---------------- logging / feedback ----------------
function Write-RigLog([string]$msg) {
    $line = '{0}  {1,-7} {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Action, $msg
    Write-Output $line
    try {
        if ((Test-Path $LogFile) -and (Get-Item $LogFile).Length -gt 200KB) {
            Move-Item $LogFile "$LogFile.old" -Force
        }
        Add-Content -Path $LogFile -Value $line
    } catch { }
}
function Fail([string]$msg) {
    Write-RigLog "ERROR: $msg"
    try { [System.Media.SystemSounds]::Hand.Play() } catch { }
    exit 1
}

# ---------------- talking to the helper ----------------
function Invoke-Rig([string]$line, [int]$timeoutMs = 3000) {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        if (-not $c.ConnectAsync('127.0.0.1', $Port).Wait(1000)) { return $null }
        $s = $c.GetStream(); $s.ReadTimeout = $timeoutMs
        $b = [Text.Encoding]::ASCII.GetBytes("$line`n"); $s.Write($b, 0, $b.Length)
        $sb = New-Object System.Text.StringBuilder
        $buf = New-Object byte[] 1024
        while ($true) {
            $n = $s.Read($buf, 0, $buf.Length)
            if ($n -le 0) { break }
            [void]$sb.Append([Text.Encoding]::ASCII.GetString($buf, 0, $n))
            if ($sb.ToString().Contains("`n")) { break }
        }
        return $sb.ToString().Trim()
    } catch { return $null } finally { $c.Close() }
}

# Send one CI-V frame. $body = command [sub] [data...].
# Returns the reply's command+data bytes (e.g. FB for OK), or $null.
function Invoke-Civ([int[]]$body) {
    $hex = ($body | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
    $r = Invoke-Rig "w $Civ $hex FD"
    if (-not $r -or $r -notmatch '^FE FE E0 98 ') { return $null }
    $bytes = @($r -split '\s+' | ForEach-Object { [Convert]::ToInt32($_, 16) })
    if ($bytes.Count -lt 6) { return $null }
    return ,([int[]]$bytes[4..($bytes.Count - 2)])
}
function Test-Ack($p) { return ($null -ne $p -and $p.Count -ge 1 -and $p[0] -eq 0xFB) }

# ---------------- BCD frequency helpers (5 bytes, least significant first) ----------------
function ConvertFrom-Bcd([int[]]$b) {
    [long]$hz = 0; [long]$mult = 1
    foreach ($x in $b) {
        $hz += (($x -band 0x0F) + 10 * (($x -shr 4) -band 0x0F)) * $mult
        $mult *= 100
    }
    return $hz
}
function ConvertTo-Bcd([long]$hz) {
    $out = New-Object int[] 5
    for ($i = 0; $i -lt 5; $i++) {
        $two = [int]($hz % 100)
        $out[$i] = ([int][math]::Floor($two / 10) -shl 4) -bor ($two % 10)
        $hz = [long][math]::Floor($hz / 100)
    }
    return ,$out
}

# ---------------- radio reads / writes ----------------
function Get-Freq {
    $p = Invoke-Civ @(0x03)
    if ($null -eq $p -or $p.Count -lt 6 -or $p[0] -ne 0x03) { return $null }
    return ConvertFrom-Bcd $p[1..5]
}
function Get-Mode {        # @{ Mode; Filter }
    $p = Invoke-Civ @(0x04)
    if ($null -eq $p -or $p.Count -lt 3 -or $p[0] -ne 0x04) { return $null }
    return @{ Mode = $p[1]; Filter = $p[2] }
}
function Get-DataMode {    # @{ Data; Filter }
    $p = Invoke-Civ @(0x1A, 0x06)
    if ($null -eq $p -or $p.Count -lt 4 -or $p[0] -ne 0x1A -or $p[1] -ne 0x06) { return $null }
    return @{ Data = $p[2]; Filter = $p[3] }
}
function Set-Freq([long]$hz) {
    if (Test-Ack (Invoke-Civ (@(0x05) + (ConvertTo-Bcd $hz)))) { return $true }
    # No OK seen (happens just after the helper starts): check what the radio did
    Start-Sleep -Milliseconds 200
    return ((Get-Freq) -eq $hz)
}
function Set-Mode([int]$mode, [int]$filter) {
    return Test-Ack (Invoke-Civ @(0x06, $mode, $filter))
}
# Mode change, sent twice: on a mode change the radio can restore that mode's
# last-used filter after applying ours (seen USB-D1 -> CW giving FIL2, not FIL3).
# The second send is to an unchanged mode, so the filter sticks.
function Set-ModeFirm([int]$mode, [int]$filter) {
    $null = Set-Mode $mode $filter
    Start-Sleep -Milliseconds 150
    $null = Set-Mode $mode $filter
    # Judge success by what the radio now reports, not by the OK replies
    $now = Get-Mode
    return ($null -ne $now -and $now.Mode -eq $mode -and $now.Filter -eq $filter)
}
function Set-DataMode([int]$data, [int]$filter) {
    if ($data -eq 0) { $filter = 0 }   # guide: data OFF must be sent with filter 00
    return Test-Ack (Invoke-Civ @(0x1A, 0x06, $data, $filter))
}
function Get-BandStack([int]$code) {   # returns the 18-byte reply payload, or $null
    $p = Invoke-Civ @(0x1A, 0x01, $code, 0x01)
    if ($null -eq $p -or $p.Count -lt 18 -or $p[0] -ne 0x1A -or $p[1] -ne 0x01) { return $null }
    return ,$p
}
function Find-Band([long]$hz) {
    foreach ($k in $Bands.Keys) {
        if ($hz -ge $Bands[$k].Lo -and $hz -le $Bands[$k].Hi) { return $k }
    }
    return $null
}

function Select-Main { return Test-Ack (Invoke-Civ @(0x07, 0xD0)) }
function Get-Split {          # 1 = on, 0 = off, $null = unknown
    $p = Invoke-Civ @(0x0F)
    if ($null -eq $p -or $p.Count -lt 2 -or $p[0] -ne 0x0F) { return $null }
    return $p[1]
}
function Set-Split([int]$on) { return Test-Ack (Invoke-Civ @(0x0F, $on)) }
function Get-SubFreq {
    $p = Invoke-Civ @(0x25, 0x01)
    if ($null -eq $p -or $p.Count -lt 7 -or $p[0] -ne 0x25) { return $null }
    return ConvertFrom-Bcd $p[2..6]
}
function Clear-SplitIfOn([string]$why) {
    if ((Get-Split) -eq 1) {
        if (Set-Split 0) { Write-RigLog "split OFF ($why)" }
        else { Fail "split is ON and could not be turned off - $why cancelled" }
    }
}
function Find-HamBand([long]$hz) {      # US amateur band containing $hz, or $null
    foreach ($k in $Bands.Keys) {
        if ($hz -ge $Bands[$k].Lo2 -and $hz -le $Bands[$k].Hi2) { return $k }
    }
    return $null
}

# ---------------- helper process management ----------------
function Get-HelperProcs {
    @(Get-CimInstance Win32_Process -Filter "Name='rigplane.exe' OR Name='python.exe' OR Name='pythonw.exe'" |
        Where-Object { $_.CommandLine -like '*rigcontrol*' -and $_.CommandLine -like '* serve *' })
}
function Stop-Helper {
    foreach ($p in Get-HelperProcs) { & taskkill.exe /PID $p.ProcessId /T /F 2>$null | Out-Null }
}
function Start-Helper {
    if (-not (Test-Path $Exe))      { Fail "rigplane not installed: $Exe" }
    if (-not (Test-Path $CredFile)) { Fail "no saved credentials - run: rig.ps1 setup" }
    $cred = Import-Clixml $CredFile
    $env:ICOM_PASS = $cred.GetNetworkCredential().Password    # inherited by the helper only
    $argList = @('--backend', 'lan', '--model', 'IC-7610', '--host', $RadioIP,
                 '--user', $cred.UserName,
                 'serve', '--host', '127.0.0.1', '--port', "$Port", '--log-level', 'WARNING')
    Start-Process -FilePath $Exe -ArgumentList $argList -WindowStyle Hidden -WorkingDirectory $Root
    Remove-Item Env:ICOM_PASS -ErrorAction SilentlyContinue
}
# Make sure a helper is running and the radio is actually answering.
function Confirm-Helper {
    if ($null -ne (Get-Freq)) { return }
    Write-RigLog 'helper not answering - (re)starting'
    Stop-Helper
    Start-Sleep -Milliseconds 500
    Start-Helper
    $deadline = (Get-Date).AddSeconds(25)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 750
        if ($null -ne (Get-Freq)) {
            Start-Sleep -Seconds 2      # let the helper finish settling before writes
            Write-RigLog 'helper ready'; return
        }
    }
    Fail 'helper did not come up within 25 s (radio on? Network Control ON? password?)'
}

# ---------------- actions ----------------
function Invoke-Band([string]$name) {
    $name = $name -replace '[mM]$', ''
    if (-not $Bands.Contains($name)) { Fail "unknown band '$name'" }
    $target = $Bands[$name]

    Clear-SplitIfOn "band change"
    $f = Get-Freq; $m = Get-Mode
    if ($null -eq $f -or $null -eq $m) { Fail 'could not read radio state' }
    $cur = Find-Band $f
    if ($cur -eq $name) { Write-RigLog "already on $name m"; return }

    # 1. Save where we are into the departing band's register 1 (front-panel behavior)
    if ($cur) {
        $code = $Bands[$cur].Code
        $old = Get-BandStack $code
        if ($old) {
            $data = 0
            if ($DataCapable -contains $m.Mode) { $d = Get-DataMode; if ($d) { $data = $d.Data } }
            $flag = (($data -band 0x0F) -shl 4) -bor ($old[11] -band 0x0F)   # keep tone type
            $frame = @(0x1A, 0x01, $code, 0x01) + (ConvertTo-Bcd $f) +
                     @($m.Mode, $m.Filter, $flag) + $old[12..17]               # keep tone freqs
            if (Test-Ack (Invoke-Civ $frame)) { Write-RigLog "saved $cur m register: $f Hz" }
            else { Write-RigLog "WARNING: could not save $cur m register (continuing)" }
        }
    }

    # 2. Recall the target band's register 1
    $r = Get-BandStack $target.Code
    if ($null -eq $r) { Fail "could not read $name m band-stack register" }
    $hz = ConvertFrom-Bcd $r[4..8]; $mode = $r[9]; $fil = $r[10]; $data = ($r[11] -shr 4) -band 0x0F
    if (-not (Set-Freq $hz))         { Fail "radio rejected frequency $hz" }
    if (-not (Set-ModeFirm $mode $fil)) { Fail "radio rejected mode $mode/FIL$fil" }
    if ($DataCapable -contains $mode) {
        if (-not (Set-DataMode $data $fil)) { Write-RigLog "WARNING: data mode $data not confirmed" }
    }
    Write-RigLog ("{0} m -> {1:N0} Hz {2}{3} FIL{4}" -f $name, $hz, $ModeNames[[int]$mode],
                  $(if ($data) { "-D$data" } else { '' }), $fil)
}

function Invoke-ModeButton([string]$which) {
    Clear-SplitIfOn "mode change"
    switch ($which.ToUpper()) {
        'SSB'  {
            # LSB below 10 MHz (160/80/40 m), USB from 10 MHz up; 60 m is USB by rule
            $f = Get-Freq
            if ($null -eq $f) { Fail 'could not read frequency' }
            $sb = 1
            if ($f -lt 10000000 -and -not ($f -ge 5250000 -and $f -le 5450000)) { $sb = 0 }
            $ok = (Set-ModeFirm $sb 2) -and (Set-DataMode 0 0)
            $which = $ModeNames[$sb]
        }
        'USB'  { $ok = (Set-ModeFirm 1 2) -and (Set-DataMode 0 0) }
        'LSB'  { $ok = (Set-ModeFirm 0 2) -and (Set-DataMode 0 0) }
        'CW'   { $ok = (Set-ModeFirm 3 3) }
        'DATA' { $ok = (Set-ModeFirm 1 1) -and (Set-DataMode 1 1) }
        default { Fail "unknown mode '$which' (SSB, USB, LSB, CW or DATA)" }
    }
    if (-not $ok) { Fail "radio did not confirm mode $which" }
    $now = Get-Mode
    if ($now) { Write-RigLog ("mode {0} (radio reports {1} FIL{2})" -f $which, $ModeNames[[int]$now.Mode], $now.Filter) }
    else      { Write-RigLog "mode $which" }
}

function Invoke-FilterStep {
    $m = Get-Mode
    if ($null -eq $m) { Fail 'could not read mode' }
    $next = ($m.Filter % 3) + 1
    $d = $null
    if ($DataCapable -contains $m.Mode) { $d = Get-DataMode }
    if ($d -and $d.Data -gt 0) { $ok = Set-DataMode $d.Data $next }   # keeps DATA on
    else                       { $ok = Set-Mode $m.Mode $next }
    if (-not $ok) { Fail "radio did not confirm FIL$next" }
    Write-RigLog "FIL$($m.Filter) -> FIL$next"
}

function Invoke-Step([long]$delta) {
    Clear-SplitIfOn "frequency step"
    $f = Get-Freq
    if ($null -eq $f) { Fail 'could not read frequency' }
    $new = $f + $delta
    # Inside a US amateur band: stop at the band edge instead of leaving the band
    foreach ($k in $Bands.Keys) {
        $b = $Bands[$k]
        if ($f -ge $b.Lo2 -and $f -le $b.Hi2) {
            if ($new -gt $b.Hi2) { $new = $b.Hi2 }
            if ($new -lt $b.Lo2) { $new = $b.Lo2 }
            break
        }
    }
    if ($new -eq $f) { Write-RigLog ("already at band edge {0:N0} Hz" -f $f); return }
    if ($new -lt 30000 -or $new -gt 60000000) { Fail "out of range: $new Hz" }
    if (-not (Set-Freq $new)) { Fail "radio rejected $new Hz" }
    Write-RigLog ("{0:N0} -> {1:N0} Hz" -f $f, $new)
}

function Invoke-Split([string]$which) {
    switch ($which.ToUpper()) {
        'SSB' { $offset = 5000 }
        'CW'  { $offset = 1000 }
        'OFF' {
            if (-not (Set-Split 0)) { Fail 'radio did not confirm split OFF' }
            Write-RigLog 'split OFF'; return
        }
        default { Fail "unknown split '$which' (SSB, CW or OFF)" }
    }
    if (-not (Select-Main)) { Fail 'could not select MAIN' }
    $f = Get-Freq
    if ($null -eq $f) { Fail 'could not read MAIN frequency' }
    $band = Find-HamBand $f
    if (-not $band) { Fail ("{0:N0} Hz is not inside a US amateur band - split not set" -f $f) }
    $tx = $f + $offset
    if ($tx -gt $Bands[$band].Hi2) {
        Fail ("split up {0} kHz would put transmit at {1:N0} Hz, above the {2} m band edge - not set" -f ($offset / 1000), $tx, $band)
    }
    # Copy MAIN to SUB (frequency, mode, filter), move SUB up, back to MAIN, split ON
    if (-not (Test-Ack (Invoke-Civ @(0x07, 0xB1)))) { Fail 'could not copy MAIN to SUB' }
    if (-not (Test-Ack (Invoke-Civ @(0x07, 0xD1)))) { $null = Select-Main; Fail 'could not select SUB' }
    $okF = Set-Freq $tx
    $okM = Select-Main
    if (-not $okM) { Fail 'could not reselect MAIN - check the radio' }
    if (-not $okF) { Fail "radio rejected SUB frequency $tx" }
    if (-not (Set-Split 1)) { Fail 'radio did not confirm split ON' }
    $sub = Get-SubFreq
    if ($sub -ne $tx) { Fail ("split ON but SUB reads {0:N0} Hz, expected {1:N0}" -f $sub, $tx) }
    Write-RigLog ("split {0}: RX {1:N0} / TX {2:N0} Hz (up {3} kHz)" -f $which.ToUpper(), $f, $tx, ($offset / 1000))
}

function Invoke-Preamp {
    $p = Invoke-Civ @(0x16, 0x02)
    if ($null -eq $p -or $p.Count -lt 3 -or $p[0] -ne 0x16) { Fail 'could not read preamp' }
    $next = ($p[2] + 1) % 3
    if (-not (Test-Ack (Invoke-Civ @(0x16, 0x02, $next)))) { Fail "radio did not confirm preamp $next" }
    $names = @('OFF', 'P.AMP1', 'P.AMP2')
    Write-RigLog ("preamp {0} -> {1}" -f $names[$p[2]], $names[$next])
}

function Invoke-Toggle([int]$sub, [string]$label) {
    $p = Invoke-Civ @(0x16, $sub)
    if ($null -eq $p -or $p.Count -lt 3 -or $p[0] -ne 0x16) { Fail "could not read $label" }
    $next = 1 - [int]($p[2] -ne 0)
    if (-not (Test-Ack (Invoke-Civ @(0x16, $sub, $next)))) { Fail "radio did not confirm $label" }
    Write-RigLog ("{0} {1}" -f $label, $(if ($next) { 'ON' } else { 'OFF' }))
}

function Invoke-Power([string]$which) {
    switch ($which.ToUpper()) {
        'OFF' {
            Confirm-Helper
            # The radio sometimes refuses the first power-off (seen 2026-10-27); try up to 3 times
            for ($i = 1; $i -le 3; $i++) {
                $null = Invoke-Civ @(0x18, 0x00)
                Start-Sleep -Seconds 3
                if ($null -eq (Get-Freq)) {
                    Stop-Helper
                    Write-RigLog "radio OFF (attempt $i); helper stopped"
                    return
                }
                Write-RigLog "power-off attempt $i not taken - retrying"
            }
            Fail 'radio still answering after 3 power-off attempts'
        }
        default { Fail "unknown power '$which' (only OFF is supported; power the radio on at the front panel)" }
    }
}

function Invoke-Setup {
    $user = Read-Host 'Radio Network User1 ID [N4MI]'
    if (-not $user) { $user = 'N4MI' }
    $pw = Read-Host 'Radio Network User1 password' -AsSecureString
    New-Object System.Management.Automation.PSCredential($user, $pw) | Export-Clixml $CredFile
    Write-RigLog "credentials saved (encrypted for this Windows user) to $CredFile"
    Stop-Helper
    Confirm-Helper
    Show-Status
}

function Show-Status {
    $procs = Get-HelperProcs
    $f = Get-Freq
    if ($null -eq $f) { Write-RigLog "helper processes: $($procs.Count); radio NOT answering"; return }
    $m = Get-Mode; $d = Get-DataMode
    $mode = $ModeNames[[int]$m.Mode]
    if ($d -and $d.Data -gt 0) { $mode += "-D$($d.Data)" }
    Write-RigLog ("helper processes: {0}; radio {1:N0} Hz {2} FIL{3}" -f $procs.Count, $f, $mode, $m.Filter)
}

# ---------------- main ----------------
# One action at a time: a second button press waits for the first to finish.
$mutex = New-Object System.Threading.Mutex($false, 'Local\N4MI_RigControl')
try { $got = $mutex.WaitOne(30000) } catch [System.Threading.AbandonedMutexException] { $got = $true }
if (-not $got) { Fail 'another rig action is still running' }
try {
    switch ($Action.ToLower()) {
        'setup'  { Invoke-Setup }
        'stop'   { Stop-Helper; Write-RigLog 'helper stopped' }
        'status' { Show-Status }
        'start'  { Confirm-Helper; Show-Status }
        'band'   { Confirm-Helper; Invoke-Band $Arg }
        'mode'   { Confirm-Helper; Invoke-ModeButton $Arg }
        'filter' { Confirm-Helper; Invoke-FilterStep }
        'up'     { Confirm-Helper; Invoke-Step $StepHz }
        'down'   { Confirm-Helper; Invoke-Step (-$StepHz) }
        'split'  { Confirm-Helper; Invoke-Split $Arg }
        'preamp' { Confirm-Helper; Invoke-Preamp }
        'nr'     { Confirm-Helper; Invoke-Toggle 0x40 'NR' }
        'nb'     { Confirm-Helper; Invoke-Toggle 0x22 'NB' }
        'power'  { Invoke-Power $Arg }
        default  { Fail "unknown action '$Action'" }
    }
} finally {
    $mutex.ReleaseMutex(); $mutex.Dispose()
}
