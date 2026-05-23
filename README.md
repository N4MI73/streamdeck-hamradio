# Stream Deck for Ham Radio — N4MI

A complete Stream Deck integration for amateur radio operators running Windows, built with PowerShell scripts and a locally-hosted propagation dashboard. One press launches your complete software stack for any operating mode, controls your antenna rotator, opens your personalized operating portal, or alerts you to severe weather threatening your tower.

Developed by **Dan Marshall, N4MI** (Grovetown, GA — EM83)
with assistance from [Claude AI](https://claude.ai/).

📖 **Full blog series:** [n4mi.tech](https://n4mi.tech)

---

## What This Does

- **One-press mode launchers** — FT8/FT4, CW, and SSB each launch their complete app stack in the correct order with the right delays, popup reminders for ACLog configuration, and automatic privilege elevation where needed
- **Clean shutdown** — closes all apps in correct dependency order with rotator return-to-North reminder and optional Python server shutdown
- **Propagation dashboard** — locally-hosted HTML page with live solar indices, band conditions, HamQSL widgets, DX cluster spots, and propagation maps, launched with one button press
- **Storm alert system** — real-time severe weather monitoring using your WeatherFlow Tempest weather station and NOAA NWS alerts, with a color-coded banner and tower safety warnings integrated directly into the dashboard
- **Rotator control** — sends azimuth commands directly to PSTRotatorAz via UDP; 8 compass direction buttons, STOP button, and 5 preset DX region headings
- **Web launcher** — opens your ham radio browser tabs (QRZ, LoTW, Clublog, PSKReporter, DX Cluster) in a dedicated Chrome profile
- **Custom icons** — full set of 144×144 PNG icons generated with Python/Pillow, consistent design language across all buttons

---

## Requirements

### Hardware
- Elgato Stream Deck (any model; 15-key MK.2 or larger recommended)
- Windows 10/11 PC
- Yaesu rotator + ERC Mini USB interface (for rotator control features)
- WeatherFlow Tempest weather station (for storm alert features — optional)

### Software (all free)
- [Stream Deck software](https://www.elgato.com/us/en/s/downloads) (Elgato)
- [Advanced Launcher plugin](https://barraider.com/) by BarRaider (from Stream Deck Plugin Store)
- [Python 3.13](https://www.python.org/downloads/) (for dashboard server and storm monitor)
  - ⚠️ Check **"Add Python to PATH"** during installation
- PowerShell 5.1 (built into Windows) or [PowerShell 7](https://github.com/PowerShell/PowerShell) (optional upgrade via `winget install Microsoft.PowerShell`)

### Ham Radio Software (paths configured in scripts)
- [ACLog](https://www.n3fjp.com/aclog.html) — N3FJP Amateur Contact Log
- [WSJT-X](https://wsjt.sourceforge.io/) — FT8/FT4 digital modes
- [JTAlert](https://hamapps.com/) — alert overlay for WSJT-X
- [MRP40](https://www.mrp40.com/) — Morse code decoder (CW workflow)
- [PSTRotatorAz](http://www.qsl.net/yo3dmu/index_Page346.htm) — rotator control software

---

## Repository Structure

```
streamdeck-hamradio/
├── README.md
├── scripts/
│   ├── HamRadioLauncher.ps1       # FT8, CW, SSB mode launchers
│   ├── HamRadioChrome.ps1         # Ham radio website launcher
│   ├── CloseHamRadio.ps1          # Clean shutdown script
│   ├── StartDashboard.ps1         # Dashboard server launcher
│   ├── RotatorAzimuth.ps1         # Antenna direction control
│   └── RotatorStop.ps1            # Stop rotation immediately
├── dashboard/
│   ├── dashboard_server.py        # Local Python web server + HamQSL proxy + storm monitor
│   └── N4MI_PropagationDashboard.html  # Propagation portal (rename callsign as needed)
└── icons/
    ├── FT8.png                    # FT8/FT4 mode launcher
    ├── SSB.png                    # SSB mode launcher
    ├── CW.png                     # CW mode launcher
    ├── WebSites.png               # Ham radio websites
    ├── N4MI_Dashboard.png         # Operating portal dashboard
    ├── CloseApps.png              # Close all apps (73)
    ├── RotatorControl.png         # Rotator control folder
    ├── RotatorStop.png            # Stop rotation
    ├── RotatorBearing.png         # Bearing query button
    ├── RadioProgramming.png       # Radio programming folder
    ├── DevManager.png             # Device Manager (COM ports)
    ├── ARCCC_NetControl.png       # K4KNS Net Control console
    ├── Dir_N.png                  # Compass direction — North (0°)
    ├── Dir_NE.png                 # Compass direction — Northeast (45°)
    ├── Dir_E.png                  # Compass direction — East (90°)
    ├── Dir_SE.png                 # Compass direction — Southeast (135°)
    ├── Dir_S.png                  # Compass direction — South (180°)
    ├── Dir_SW.png                 # Compass direction — Southwest (225°)
    ├── Dir_W.png                  # Compass direction — West (270°)
    ├── Dir_NW.png                 # Compass direction — Northwest (315°)
    ├── DX_Europe.png              # DX region — Europe (50°)
    ├── DX_WestAfrica.png          # DX region — West Africa (80°)
    ├── DX_Asia.png                # DX region — Asia (342°)
    ├── DX_SouthAmerica.png        # DX region — South America (145°)
    ├── DX_Pacific.png             # DX region — Pacific (290°)
    └── radio-programming/         # RT Systems radio icons
        ├── IC-7610.png
        ├── IC-7300.png
        ├── IC-9700.png
        ├── IC-R6.png
        ├── FTM-6000.png
        ├── ID-52.png
        ├── TH-D74.png
        ├── AT-D878.png
        ├── DJ-MD5.png
        ├── KG-935G.png
        ├── DM-32UV.png
        └── DR-06.png
```

---

## Quick Start

### 1. Copy scripts to your PC
Save all files from `scripts/` and `dashboard/` to `C:\Ham Scripts\`

### 2. Edit paths in scripts
Open each `.ps1` file in Notepad and update the app paths at the top to match your installation. Key paths to check in `HamRadioLauncher.ps1`:
```powershell
$aclog      = "C:\Program Files (x86)\N3FJP Software...\aclog.exe"
$wsjtx      = "C:\WSJT\wsjtx\bin\wsjtx.exe"
$jtalert    = "C:\Program Files (x86)\HamApps\JTAlertV2\JTAlertV2.exe"
$mrp40      = "C:\Program Files (x86)\HamRadioSoftware\MRP40...\MRP40v67.exe"
$pstrotator = "C:\Program Files (x86)\PstRotatorAz\PstRotatorAz.exe"
```

### 3. Configure the dashboard
Edit `dashboard_server.py` and update the storm alert settings at the top:
```python
TEMPEST_TOKEN      = "YOUR_TOKEN_HERE"   # From tempestwx.com > Settings > Data Authorizations
TEMPEST_STATION_ID = "YOUR_STATION_ID"  # Visible in the Tempest app
NWS_ZONE           = "GAC073"           # Your county — find at api.weather.gov/points/{lat},{lon}
```
If you don't have a Tempest station, the dashboard still works — storm alerts will simply not activate.

### 4. Configure Stream Deck buttons
For each button, use the **Advanced Launcher** plugin with:
- **Executable:** `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
- **Arguments:** `-ExecutionPolicy Bypass -File "C:\Ham Scripts\ScriptName.ps1" -mode ft8`

Example arguments for each mode:
```
FT8:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ft8
CW:   -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode cw
SSB:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ssb
```

### 5. Configure PSTRotatorAz for UDP control
In PSTRotatorAz: **Setup → UDP Control** (check the box), then **Communication → UDP Control Port → 12000**

### 6. Customize the dashboard
Edit `N4MI_PropagationDashboard.html` and update the callsign and grid square to your own. Update `CALLSIGN` in `dashboard_server.py` as well.

---

## Script Reference

| Script | Purpose | Key Arguments |
|--------|---------|---------------|
| `HamRadioLauncher.ps1` | Launches complete app stack for a mode | `-mode ft8` / `-mode cw` / `-mode ssb` |
| `HamRadioChrome.ps1` | Opens ham radio websites in Chrome | none |
| `CloseHamRadio.ps1` | Cleanly shuts down all ham radio apps | none |
| `StartDashboard.ps1` | Starts Python server and opens dashboard | none |
| `RotatorAzimuth.ps1` | Rotates antenna to any azimuth | `-az 270` (0–360) |
| `RotatorStop.ps1` | Immediately stops antenna rotation | none |

---

## Storm Alert System

The dashboard includes a real-time storm monitoring system that combines two data sources:

**WeatherFlow Tempest API** — polls your personal weather station every 60 seconds for lightning distance, strike rate, and wind speed.

**NOAA NWS Alerts API** — polls active weather alerts for your county every 120 seconds. Free, no API key required.

### Alert Levels

| Level | Color | Trigger | Action Recommended |
|-------|-------|---------|-------------------|
| CAUTION | Yellow | Lightning within 80 km, wind gust >35 mph, or NWS statement | Monitor conditions |
| WARNING | Orange | Lightning within 40 km, or NWS Severe Thunderstorm/Tornado Watch | Consider lowering tower |
| CRITICAL | Red (flashing) | NWS Severe Thunderstorm Warning, Tornado Warning, or Tornado Emergency | Lower tower immediately |

When an alert is active, a full-width banner appears at the top of the dashboard showing lightning distance in km and miles, time since last strike, strike rate per hour, wind gust, and the full NWS alert headline. A Storm Status indicator in the solar bar is always visible even when no alert is active.

### Finding Your NWS Zone
Visit `https://api.weather.gov/points/{latitude},{longitude}` and look for the `forecastZone` field. The zone code (e.g. `GAC073`) goes in `NWS_ZONE` in `dashboard_server.py`.

### Security Note
Never commit your Tempest API token to a public repository. The token in this repo is a placeholder (`YOUR_TOKEN_HERE`). Generate your personal token at tempestwx.com → Settings → Data Authorizations.

---

## DX Region Headings (from EM83 — Central Georgia)

These are approximate great-circle headings. Operators in other grid squares should calculate their own using ACLog, PSTRotatorAz's DXCC lookup, or an online great-circle calculator.

| Region | Azimuth |
|--------|---------|
| Europe | 50° |
| West Africa | 80° |
| S. America | 145° |
| Pacific | 290° |
| Asia | 342° |

---

## Customizing for Your Station

- **App paths** — update in `HamRadioLauncher.ps1` and `CloseHamRadio.ps1`
- **COM ports** — the CW popup reminder references COM 6 (IC-7610) and COM 10 (WinKeyer). Update popup text in `HamRadioLauncher.ps1` to match your setup
- **UDP port** — default is 12000. Change `$udpPort` in `RotatorAzimuth.ps1` and `RotatorStop.ps1` if your PSTRotatorAz uses a different port
- **Chrome profile** — default is `Profile 1`. Update `$profile` in `HamRadioChrome.ps1` and `StartDashboard.ps1`
- **Dashboard callsign/grid** — update in both `dashboard_server.py` and `N4MI_PropagationDashboard.html`
- **DX region azimuths** — update `-az` arguments in your Stream Deck button configurations
- **Launch delays** — adjust `$shortDelay` and `$jtalertDelay` in `HamRadioLauncher.ps1` if apps need more time to load on your PC
- **Storm thresholds** — adjust `LIGHTNING_WARNING_KM`, `LIGHTNING_CAUTION_KM`, and `LIGHTNING_RECENT_MINS` in `dashboard_server.py`
- **NWS zone** — update `NWS_ZONE` in `dashboard_server.py` to your county's zone code

---

## Blog Series

Full writeups with setup instructions, screenshots, and explanations at **[n4mi.tech](https://n4mi.tech)**:

1. Stream Deck Basics — Mode Launchers & PowerShell Scripts
2. The Personal Operating Portal — Propagation Dashboard
3. Rotator Control from the Stream Deck
4. Storm Alert Integration — Tower Safety with Tempest + NWS
5. Custom Icons, Getting Started & Closing Thoughts

---

## License

MIT License — free to use, modify, and share. If you adapt this for your own station, a mention of N4MI is appreciated but not required. 73!

---

*Developed with assistance from [Claude AI](https://claude.ai/) — Anthropic*
