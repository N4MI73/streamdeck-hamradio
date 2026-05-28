# Stream Deck for Ham Radio — N4MI

A complete Stream Deck integration for amateur radio operators running Windows, built with PowerShell scripts and a locally-hosted propagation dashboard. One press launches your complete software stack for any operating mode, controls your antenna rotator, or opens your personalized operating portal.

Developed by **Dan Marshall, N4MI** (Grovetown, GA — EM83)
with assistance from [Claude AI](https://claude.ai/).

📖 **Full blog series:** [n4mi.tech](https://n4mi.tech)

---

## What This Does

- **One-press mode launchers** — FT8/FT4, CW, and SSB each launch their complete app stack in the correct order with the right delays, popup reminders for ACLog configuration, and automatic privilege elevation where needed
- **Clean shutdown** — closes all apps in correct dependency order with rotator return-to-North reminder
- **Propagation dashboard** — locally-hosted HTML page with live solar indices, band conditions, DX cluster spots, and propagation maps, launched with one button press
- **Storm alert system** — three-level alert banner (CAUTION / WARNING / CRITICAL) using WeatherFlow Tempest lightning data and NOAA NWS alerts; warns when it's time to lower the tower
- **Rotator control** — sends azimuth commands directly to PSTRotatorAz via UDP; compass direction buttons plus preset DX region headings
- **Web launcher** — opens your ham radio browser tabs (QRZ, LoTW, Clublog, PSKReporter, DX Cluster) in a dedicated Chrome profile
- **HamShackFeed** — single-file ham radio content aggregator; pulls blogs, podcasts, and YouTube channels into one searchable dashboard with favorites, read tracking, and a built-in podcast player
- **Custom icons** — full set of 144×144 PNG icons generated with Python/Pillow, consistent design language across all buttons

---

## Requirements

### Hardware

- Elgato Stream Deck (any model; 15-key MK.2 or larger recommended)
- Windows 10/11 PC
- Yaesu rotator + ERC Mini USB interface (for rotator control features)

### Software (all free)

- [Stream Deck software](https://www.elgato.com/us/en/s/downloads) (Elgato)
- [Advanced Launcher plugin](https://barraider.com/) by BarRaider (from Stream Deck Plugin Store)
- [Python 3.13](https://www.python.org/downloads/) (for dashboard server)
  * ⚠️ Check **"Add Python to PATH"** during installation
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
│   ├── dashboard_server.py        # Local Python web server + DX cluster proxy
│   ├── N4MI_PropagationDashboard.html  # Propagation portal (rename callsign as needed)
│   └── HamShackFeed.html          # Ham radio content aggregator (see setup below)
└── icons/
    ├── FT8.png
    ├── SSB.png
    ├── CW.png
    ├── WebSites.png
    ├── N4MI_Dashboard.png
    ├── CloseApps.png
    ├── RotatorControl.png
    ├── RotatorStop.png
    ├── RotatorBearing.png
    ├── RadioProgramming.png
    ├── RT.png
    ├── DevManager.png
    ├── ARCCC_NetControl.png
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
    └── radio-programming/
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

```
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

### 6. Set up HamShackFeed

See the [HamShackFeed Setup](#hamshackfeed-setup) section below.

---

## HamShackFeed Setup

HamShackFeed is a single HTML file that aggregates ham radio blogs, podcasts, and YouTube channels into one searchable dashboard. It works by fetching RSS feeds through the [rss2json.com](https://rss2json.com) API proxy.

### Why an API key is required

The file in this repo ships with a placeholder API key (`YOUR_RSS2JSON_API_KEY_HERE`). Without a real key, the proxy is rate-limited to **1 request per 10 seconds** — which means the default sources will load slowly and **adding new sources will consistently fail**.

A free rss2json.com account gives you **10,000 requests per day**, which is more than enough for normal use.

### Getting your free API key

1. Go to [https://rss2json.com](https://rss2json.com)
2. Click **Sign Up** and create a free account
3. After logging in, your API key is shown on the dashboard
4. Copy the key — it looks like: `u8ek4zaqygaq9omwvw4axvmyeqiiypogmj5b1ktx`

### Adding your key to HamShackFeed

Open `HamShackFeed.html` in a text editor and find this line near the top of the `<script>` block (around line 1020):

```javascript
const RSS2JSON_KEY = 'YOUR_RSS2JSON_API_KEY_HERE';
```

Replace the placeholder with your actual key:

```javascript
const RSS2JSON_KEY = 'your_actual_key_here';
```

Save the file. That's it — all feed fetching and the **+ Add Source** button will now work correctly.

### Adding sources

Open the file in your browser and click **+ Add Source**. Paste any of the following:

- A blog URL — e.g. `https://www.kb6nu.com` (HamShackFeed tries `/feed` automatically for WordPress sites)
- A direct RSS/Atom feed URL — e.g. `https://www.arrl.org/arrl.rss`
- A Podbean or Spreaker podcast URL — feed is constructed automatically
- A YouTube channel URL — e.g. `https://youtube.com/channel/UCxxxxx` (channel ID format works best)

> **Note:** YouTube handle URLs (`@channelname`) cannot be auto-converted to a feed without the YouTube Data API. Use the full channel URL from the channel's **About** page instead.

---

## Script Reference

| Script | Purpose | Key Arguments |
| --- | --- | --- |
| `HamRadioLauncher.ps1` | Launches complete app stack for a mode | `-mode ft8` / `-mode cw` / `-mode ssb` |
| `HamRadioChrome.ps1` | Opens ham radio websites in Chrome | none |
| `CloseHamRadio.ps1` | Cleanly shuts down all ham radio apps | none |
| `StartDashboard.ps1` | Starts Python server and opens dashboard | none |
| `RotatorAzimuth.ps1` | Rotates antenna to any azimuth | `-az 270` (0–360) |
| `RotatorStop.ps1` | Immediately stops antenna rotation | none |

---

## DX Region Headings (from EM83 — Central Georgia)

These are approximate great-circle headings. Operators in other grid squares should calculate their own using ACLog, PSTRotatorAz's DXCC lookup, or an online great-circle calculator.

| Region | Azimuth |
| --- | --- |
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
- **HamShackFeed API key** — set `RSS2JSON_KEY` in `HamShackFeed.html` as described above.

---

## Blog Series

Full writeups with setup instructions, screenshots, and explanations at **[n4mi.tech](https://n4mi.tech)**:

1. Stream Deck Basics — Mode Launchers & PowerShell Scripts
2. The Personal Operating Portal — Propagation Dashboard
3. Rotator Control from the Stream Deck
4. Custom Icons, Getting Started & Closing Thoughts
5. HamShackFeed — Ham Radio Content Aggregator

---

## License

MIT License — free to use, modify, and share. If you adapt this for your own station, a mention of N4MI is appreciated but not required. 73!

---

*Developed with assistance from [Claude AI](https://claude.ai/) — Anthropic*
