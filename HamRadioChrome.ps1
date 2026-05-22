# ============================================================
#  Ham Radio Chrome Launcher
#  Save location: C:\Ham Scripts\HamRadioChrome.ps1
#
#  Opens commonly used ham radio websites in Chrome
#  using the designated Chrome profile.
#
#  Stream Deck setup (System > Open, app = powershell.exe):
#    Arguments: -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioChrome.ps1"
# ============================================================

# ---- CHROME PATH -------------------------------------------

$chrome  = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# ---- CHROME PROFILE ----------------------------------------

$profile = "Profile 1"

# ---- URLS TO OPEN ------------------------------------------

$urls = @(
    "https://www.qrz.com/lookup",
    "https://lotw.arrl.org/lotwuser/default",
    "https://clublog.org/loginform.php",
    "https://pskreporter.info/pskmap.html",
    "http://dxsummit.fi/#/",
    "https://holycluster.iarc.org/"
)

# ============================================================

if (-not (Test-Path $chrome)) {
    Write-Host "WARNING: Chrome not found at:" -ForegroundColor Yellow
    Write-Host "  $chrome" -ForegroundColor Yellow
    Write-Host "  Please update the chrome path in the script." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    exit
}

Write-Host "`n=== Launching Ham Radio Browser Tabs ===" -ForegroundColor Magenta

# Build the argument list - first URL opens Chrome, rest are additional tabs
$arguments = "--profile-directory=`"$profile`" " + ($urls -join " ")

Write-Host "Opening $($urls.Count) tabs in Chrome Profile: $profile" -ForegroundColor Green
Start-Process $chrome -ArgumentList $arguments

Write-Host "`nAll tabs launched! 73!" -ForegroundColor Green
Start-Sleep -Seconds 3
