# Stream Deck for Ham Radio — N4MI

A complete Stream Deck integration for amateur radio operators running Windows, built with PowerShell scripts and a locally-hosted propagation and storm alert dashboard. One press launches your complete software stack for any operating mode, controls your antenna rotator, or opens your personalized operating portal.

Developed by **Dan Marshall, N4MI** (Grovetown, GA — EM83)
with assistance from [Claude AI](https://claude.ai/).

📖 **Full blog series:** [n4mi.tech](https://n4mi.tech)

---

## What This Does

- **One-press mode launchers** — FT8/FT4, CW, and SSB each launch their complete app stack in the correct order with the right delays, popup reminders for ACLog configuration, and automatic privilege elevation where needed
- **Clean shutdown** — closes all apps in correct dependency order with rotator return-to-North reminder
- **Propagation dashboard** — locally-hosted HTML page with live solar indices, band conditions, DX cluster spots, and propagation maps, launched with one button press
- **Storm alert system** — integrated real-time weather monitoring via WeatherFlow Tempest and NOAA NWS alerts, with tower safety warnings displayed directly in the dashboard
- **Rotator control** — sends azimuth commands directly to PSTRotatorAz via UDP; compass direction buttons plus preset DX region headings
- **Web launcher** — opens your ham radio browser tabs (QRZ, LoTW, Clublog, PSKReporter, DX Cluster) in a dedicated Chrome profile
- **HamShackFeed** — single-file HTML RSS aggregator for ham radio blogs, podcasts, and YouTube channels
- **Custom icons** — full set of 144×144 PNG icons generated with Python/Pillow, consistent design language across all buttons

---

## Requirements

### Hardware
- Elgato Stream Deck (any model; 15-key MK.2 or larger recommended)
- Windows 10/11 PC
- Yaesu rotator + ERC Mini USB interface (for rotator control features)
- [WeatherFlow Tempest](https://weatherflow.com/tempest-weather-system/) personal weather station (optional — for storm alert system)

### Software (all free)
- [Stream Deck software](https://www.elgato.com/us/en/s/downloads) (Elgato)
- [Advanced Launcher plugin](https://barraider.com/) by BarRaider (from Stream Deck Plugin Store)
- [Python 3.13](https://www.python.org/downloads/) (for dashboard server)
  - ⚠️ Check **"Add Python to PATH"** during installation
- PowerShell 5.1 (built into Windows) or [PowerShell 7](https://github.com/PowerShell/PowerShell) (optional upgrade)

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
│   ├── dashboard_server.py        # Local Python web server + DX cluster proxy + storm monitor
│   ├── N4MI_PropagationDashboard.html  # Propagation portal (rename callsign as needed)
│   └── HamShackFeed.html          # Ham radio RSS content aggregator
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
    ├── RT.png                     # RT Systems launcher
    ├── DevManager.png             # Device Manager (COM ports)
    ├── ARCCC_NetControl.png       # K4KNS Net Control
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

### 3. Configure Stream Deck buttons
For each button, use the **Advanced Launcher** plugin with:
- **Executable:** `powershell.exe`
- **Arguments:** `-ExecutionPolicy Bypass -File "C:\Ham Scripts\ScriptName.ps1" -mode ft8`

Example arguments for each mode:
```
FT8:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ft8
CW:   -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode cw
SSB:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ssb
```

### 4. Configure PSTRotatorAz for UDP control
In PSTRotatorAz: **Communication → UDP Control → Enable**, port **12000**

### 5. Customize the dashboard
Edit `N4MI_PropagationDashboard.html` and update the callsign and grid square to your own. Update the callsign in `dashboard_server.py` as well (`CALLSIGN = "N4MI"`).

### 6. Configure the storm alert system (optional)
If you have a WeatherFlow Tempest station, update these settings at the top of `dashboard_server.py`:
```python
TEMPEST_TOKEN      = "YOUR_TEMPEST_TOKEN_HERE"   # From tempestwx.com → Settings → Data Authorizations
TEMPEST_STATION_ID = "YOUR_STATION_ID"           # Your Tempest station ID
NWS_ZONE           = "GAC073"                    # Your NWS zone — find at weather.gov
```
If you don't have a Tempest station, the dashboard will still display NWS alerts — just leave the Tempest fields as placeholders.

### 7. Open HamShackFeed
Save `HamShackFeed.html` to `C:\Ham Scripts\` and open it directly in Chrome. No server required. Bookmark `file:///C:/Ham%20Scripts/HamShackFeed.html` for easy access.

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

## Storm Alert Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `TEMPEST_TOKEN` | YOUR_TEMPEST_TOKEN_HERE | WeatherFlow API personal access token |
| `TEMPEST_STATION_ID` | YOUR_STATION_ID | Your Tempest station ID |
| `NWS_ZONE` | GAC073 | NWS zone code for your county |
| `NWS_POLL_SECONDS` | 120 | How often to check NWS alerts |
| `TEMPEST_POLL_SECONDS` | 60 | How often to check Tempest data |
| `LIGHTNING_WARNING_KM` | 40 | Distance for WARNING level (km) |
| `LIGHTNING_CAUTION_KM` | 80 | Distance for CAUTION level (km) |
| `LIGHTNING_RECENT_MINS` | 30 | Max age of strike to be considered active (min) |

Find your NWS zone code at [weather.gov](https://www.weather.gov) → your local forecast office → zone forecast page.

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
- **COM ports** — the CW popup reminder references COM 6 (IC-7610) and COM 10 (WinKeyer). Update popup text in `HamRadioLauncher.ps1` to match your setup.
- **UDP port** — default is 12000. Change `$udpPort` in `RotatorAzimuth.ps1` and `RotatorStop.ps1` if your PSTRotatorAz uses a different port.
- **Chrome profile** — default is `Profile 1`. Update `$profile` in `HamRadioChrome.ps1` and `StartDashboard.ps1`.
- **Dashboard callsign/grid** — update in both `dashboard_server.py` and `N4MI_PropagationDashboard.html`.
- **DX region azimuths** — update `-az` arguments in your Stream Deck button configurations.
- **Launch delays** — adjust `$shortDelay` and `$jtalertDelay` in `HamRadioLauncher.ps1` if apps need more time to load on your PC.
- **Tempest API token** — replace `YOUR_TEMPEST_TOKEN_HERE` in `dashboard_server.py` with your personal access token from tempestwx.com → Settings → Data Authorizations
- **Tempest station ID** — replace `YOUR_STATION_ID` with your station ID found at tempestwx.com
- **NWS zone code** — default is `GAC073` (Columbia County GA). Find your zone at weather.gov
- **Lightning thresholds** — adjust `LIGHTNING_WARNING_KM` (default 40km) and `LIGHTNING_CAUTION_KM` (default 80km) to suit your preference
- **HamShackFeed sources** — add or remove RSS sources using the built-in Add Source button in the dashboard

---

## Blog Series

Full writeups with setup instructions, screenshots, and explanations at **[n4mi.tech](https://n4mi.tech)**:

1. [Stream Deck for Ham Radio — Part 1: Mode Launchers & PowerShell Scripts](https://n4mi.tech/integrating-elgato-stream-deck-with-amateur-radio/)
2. [Stream Deck for Ham Radio — Part 2: A Live Propagation Dashboard](https://n4mi.tech/stream-deck-for-ham-radio-part-2-a-live-propagation-dashboard/)
3. [Stream Deck for Ham Radio — Part 3: Rotator Control](https://n4mi.tech/stream-deck-for-ham-radio-part-3-rotator-control/)
4. [Stream Deck for Ham Radio — Part 4: HamShackFeed — My Personal Ham Radio Newsroom](https://n4mi.tech/stream-deck-for-ham-radio-part-4-hamshackfeed-my-personal-ham-radio-newsroom/)
5. [Stream Deck for Ham Radio — Part 5: Custom Icons, Getting Started & Closing Thoughts](https://n4mi.tech/stream-deck-for-ham-radio-part-5-custom-icons-getting-started-closing-thoughts/)

---

## License

MIT License — free to use, modify, and share. If you adapt this for your own station, a mention of N4MI is appreciated but not required. 73!

---

*Developed with assistance from [Claude AI](https://claude.ai/) — Anthropic*
