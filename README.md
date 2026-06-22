# Stream Deck for Ham Radio — N4MI

A complete Stream Deck integration for amateur radio operators running Windows, built with PowerShell scripts, a locally-hosted propagation dashboard, and a server-powered ham radio content aggregator. One press launches your complete software stack for any operating mode, controls your antenna rotator, or opens your personalized operating portal.

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
- **HamShackFeed Pro** — server-powered version of HamShackFeed with SQLite persistence, direct RSS fetching (no API key needed), background refresh, and cross-device access
- **ManualShelf** — locally-hosted PDF and image manual catalog; browse, search, tag, and open radio manuals and settings screenshots with auto-generated thumbnails; cross-computer visibility via NAS exchange folder
- **Custom icons** — full set of 144×144 PNG icons generated with Python/Pillow, consistent design language across all buttons

---
### Before You Download
- These projects were developed for my personal ham radio station and computing environment.
- Many components contain settings, file paths, hardware references, API keys, COM ports, network addresses, and other configuration details specific to my station.
- Think of these projects as examples and starting points rather than turnkey applications.
- Most users should expect to customize the software for their own station, operating style, and computer environment.
- The good news is that modern AI assistants such as Claude, ChatGPT, Gemini, or similar tools can often help adapt these projects to your specific needs much faster than building them from scratch.
- If you are comfortable experimenting and customizing, you may find these projects useful as a foundation for your own shack tools.

## Requirements

### Hardware

- Elgato Stream Deck (any model; 15-key MK.2 or larger recommended)
- Windows 10/11 PC
- Yaesu rotator + ERC Mini USB interface (for rotator control features)

### Software (all free)

- [Stream Deck software](https://www.elgato.com/us/en/s/downloads) (Elgato)
- [Advanced Launcher plugin](https://barraider.com/) by BarRaider (from Stream Deck Plugin Store)
- [Python 3.13](https://www.python.org/downloads/) (for dashboard server and HamShackFeed Pro)
  * ⚠️ Check **"Add Python to PATH"** during installation
- PowerShell 7 ([download](https://github.com/PowerShell/PowerShell)) — required for HamShackFeed Pro launcher

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
├── .gitignore
├── scripts/
│   ├── HamRadioLauncher.ps1            # FT8, CW, SSB mode launchers
│   ├── HamRadioChrome.ps1              # Ham radio website launcher
│   ├── CloseHamRadio.ps1               # Clean shutdown script
│   ├── StartDashboard.ps1              # Dashboard server launcher
│   ├── RotatorAzimuth.ps1              # Antenna direction control
│   └── RotatorStop.ps1                 # Stop rotation immediately
├── dashboard/
│   ├── dashboard_server.py             # Local Python web server + DX cluster proxy
│   ├── N4MI_PropagationDashboard.html  # Propagation portal (rename callsign as needed)
│   └── HamShackFeed.html               # Ham radio content aggregator (see setup below)
├── hamshackfeed_pro/
│   ├── server.py                       # Flask server, API routes, scheduler
│   ├── fetcher.py                      # Direct RSS parsing (no API key needed)
│   ├── requirements.txt                # Python dependencies
│   ├── import_sources.py               # Migrate sources from HamShackFeed HTML version
│   ├── StartHamShackFeedPro.ps1        # PowerShell launcher
│   └── templates/
│       └── index.html                  # Frontend
├── manualshelf/
│   ├── server.py                       # Flask server, SQLite catalog, NAS manifest
│   ├── requirements.txt                # flask, PyMuPDF, Pillow
│   ├── StartManualShelf.ps1            # Launcher (opens browser automatically)
│   ├── StopManualShelf.ps1             # Stop via PID file
│   └── templates/
│       └── index.html                  # Frontend
└── icons/
    ├── FT8.png
    ├── SSB.png
    ├── CW.png
    └── ... (see full list in repo)
```

---

## Quick Start

### 1. Copy scripts to your PC

Save all files maintaining the folder structure to `C:\Ham Scripts\`

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

- **Executable:** `pwsh.exe` (PowerShell 7) or `powershell.exe` (Windows PowerShell 5.1)
- **Arguments:** `-ExecutionPolicy Bypass -File "C:\Ham Scripts\ScriptName.ps1"`

Example arguments for mode launchers:

```
FT8:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ft8
CW:   -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode cw
SSB:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\HamRadioLauncher.ps1" -mode ssb
```

HamShackFeed Pro button:

```
Executable: pwsh.exe
Arguments:  -ExecutionPolicy Bypass -Command "cd 'C:\Ham Scripts\hamshackfeed_pro'; python server.py"
Start In:   C:\Ham Scripts\hamshackfeed_pro
```

### 4. Configure PSTRotatorAz for UDP control

In PSTRotatorAz: **Communication → UDP Control → Enable**, port **12000**

### 5. Customize the propagation dashboard

Edit `N4MI_PropagationDashboard.html` and update the callsign and grid square to your own. Update the callsign in `dashboard_server.py` as well (`CALLSIGN = "N4MI"`).

### 6. Set up HamShackFeed

See the [HamShackFeed Setup](#hamshackfeed-setup) section below.

### 7. Set up HamShackFeed Pro

See the [HamShackFeed Pro Setup](#hamshackfeed-pro-setup) section below.

### 8. Set up ManualShelf

See the [ManualShelf Setup](#manualshelf-setup) section below.

---

## HamShackFeed Setup

HamShackFeed (`dashboard/HamShackFeed.html`) is a single HTML file that aggregates ham radio blogs, podcasts, and YouTube channels. It works by fetching RSS feeds through the [rss2json.com](https://rss2json.com) API proxy.

### API key required

The file in this repo ships with a placeholder key (`YOUR_RSS2JSON_API_KEY_HERE`). Without a real key, the proxy is rate-limited to 1 request per 10 seconds — the default sources will load slowly and **adding new sources will fail**.

A free rss2json.com account gives you 10,000 requests per day.

**To get your free key:**
1. Go to [https://rss2json.com](https://rss2json.com) and sign up
2. Copy your API key from the dashboard
3. Open `HamShackFeed.html` in a text editor and find this line near the top of the `<script>` block:
```javascript
const RSS2JSON_KEY = 'YOUR_RSS2JSON_API_KEY_HERE';
```
4. Replace the placeholder with your key and save

> **Tip:** Consider using HamShackFeed Pro instead — it fetches feeds directly on the server with no API key needed, stores everything in SQLite, and works across devices.

---

## HamShackFeed Pro Setup

HamShackFeed Pro (`hamshackfeed_pro/`) is a locally-hosted server version that solves the limitations of the standalone HTML file:

| Feature | HamShackFeed | HamShackFeed Pro |
|---|---|---|
| RSS proxy API key | Required | **Not needed** |
| Source/read persistence | Browser localStorage | **SQLite database** |
| Cross-device access | No | **Yes (local network)** |
| Background refresh | No | **Every 30 minutes** |
| Port | n/a | **8074** |

### Installation

1. Copy the `hamshackfeed_pro\` folder to `C:\Ham Scripts\`

2. Install Python dependencies (run once):
```powershell
cd "C:\Ham Scripts\hamshackfeed_pro"
pip install -r requirements.txt
```

3. Start the server:
```powershell
cd "C:\Ham Scripts\hamshackfeed_pro"
python server.py
```

4. Open `http://localhost:8074` in your browser

The `hamshackfeed.db` SQLite database is created automatically on first run. Feeds begin loading in the background immediately.

### Accessing from other devices

HamShackFeed Pro binds to all network interfaces. From any device on your local network, open:
```
http://192.168.x.x:8074
```
Replace with your ham computer's local IP. Read state and sources are shared across all devices.

> **Windows Firewall:** If other devices can't connect, allow inbound connections on port 8074:
> ```powershell
> New-NetFirewallRule -DisplayName "HamShackFeed Pro" -Direction Inbound -Protocol TCP -LocalPort 8074 -Action Allow
> ```

### Migrating sources from HamShackFeed HTML version

1. Open `HamShackFeed.html` in your browser, press `F12`, open the Console tab, and run:
```javascript
const all = JSON.parse(localStorage.getItem('n4mi_sources_v2') || '[]');
const custom = all.filter(s => String(s.id).startsWith('custom_'));
copy(JSON.stringify(custom, null, 2));
console.log(`Copied ${custom.length} custom sources to clipboard`);
```

2. Paste into a file called `custom_sources.json` in `C:\Ham Scripts\hamshackfeed_pro\`

3. With the Pro server running, execute:
```powershell
cd "C:\Ham Scripts\hamshackfeed_pro"
python import_sources.py
```

### Adding YouTube channels

Use the full channel URL format — YouTube handle URLs (`@name`) cannot be auto-resolved:

✅ `https://www.youtube.com/channel/UCxxxxxxxxxxxxxxx`  
❌ `https://www.youtube.com/@channelname`

Find the channel URL on the channel's About page.

---

## ManualShelf Setup

ManualShelf (`manualshelf/`) is a locally-hosted catalog for PDF manuals and settings screenshots. It generates thumbnails from PDF first pages, supports tagging and search, and can show manuals available on another computer via a shared NAS folder.

| Feature | Detail |
|---|---|
| Port | **8075** |
| Supported files | PDF, PNG, JPG, GIF, BMP, WEBP, DOCX, DOC, XLSX, XLS, CSV, PPTX, PPT, TXT, MD, HTML |
| In-app preview | MD and TXT files render inside the app; all others open in default Windows app |
| Full-text search | PDF text content is indexed and searchable via Re-index PDFs in Settings |
| Thumbnail generation | PyMuPDF (first page of PDF) |
| Cross-computer | NAS exchange folder manifest |

### Installation

1. Copy the `manualshelf\` folder to `C:\Ham Scripts\`

2. Install Python dependencies (run once):
```powershell
cd "C:\Ham Scripts\manualshelf"
pip install -r requirements.txt
```

3. Start the server:
```powershell
.\StartManualShelf.ps1
```

Or run directly: `python server.py`

Open `http://localhost:8075` in your browser.

### First-time setup

1. Click **⚙ Settings** — set your Computer Name and optionally a NAS Exchange Folder for cross-computer visibility
2. Click **📂 Add Manuals** — paste a folder path and scan; select files to add to the catalog
3. Thumbnails are generated automatically on add

### Updating a manual

When you replace a file on disk with a newer version, re-scan the folder. Changed files appear with an amber **UPDATE** badge, pre-checked. Selecting them refreshes the thumbnail and file data while preserving your title, tags, make, model, and category.

### Full-text PDF search

ManualShelf can search inside PDF text content, not just filenames and tags. To enable it:

1. Open **⚙ Settings** and click **🔍 Re-index PDFs** — indexing runs in the background
2. Search normally — results that matched on PDF text content show a purple **PDF TEXT** badge

New PDFs are indexed automatically when added. Re-run after adding a large batch.

### Bulk tag editor

To apply tags or a category to multiple files at once:

1. Click **☑ Select** in the toolbar to enter selection mode
2. Click cards to select them, or use **Select All**
3. Click **✏️ Edit Selected** and enter tags and/or a category
4. Check **Add to existing tags** to merge with existing tags rather than replace them
   
### Cross-computer visibility

Each running instance writes a manifest to the NAS exchange folder every 5 minutes. The other machine reads it and shows remote manuals under the **📡 Remote Manuals** sidebar filter. Clicking a remote entry shows its full metadata with a note that the file lives on the other machine and must be retrieved via LocalSend or the NAS exchange folder.

### Stream Deck button

```
Executable: powershell.exe
Arguments:  -ExecutionPolicy Bypass -File "C:\Ham Scripts\manualshelf\StartManualShelf.ps1"
Start In:   C:\Ham Scripts\manualshelf
```

---

## Script Reference

| Script | Purpose | Key Arguments |
|---|---|---|
| `HamRadioLauncher.ps1` | Launches complete app stack for a mode | `-mode ft8` / `-mode cw` / `-mode ssb` |
| `HamRadioChrome.ps1` | Opens ham radio websites in Chrome | none |
| `CloseHamRadio.ps1` | Cleanly shuts down all ham radio apps | none |
| `StartDashboard.ps1` | Starts Python server and opens dashboard | none |
| `RotatorAzimuth.ps1` | Rotates antenna to any azimuth | `-az 270` (0–360) |
| `RotatorStop.ps1` | Immediately stops antenna rotation | none |
| `hamshackfeed_pro/server.py` | Starts HamShackFeed Pro on port 8074 | none |
| `manualshelf/server.py` | Starts ManualShelf catalog on port 8075 | none |

---

## DX Region Headings (from EM83 — Central Georgia)

These are approximate great-circle headings. Operators in other grid squares should calculate their own using ACLog, PSTRotatorAz's DXCC lookup, or an online great-circle calculator.

| Region | Azimuth |
|---|---|
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
- **HamShackFeed API key** — set `RSS2JSON_KEY` in `HamShackFeed.html` (or use HamShackFeed Pro instead).
- **HamShackFeed Pro refresh interval** — change `REFRESH_INTERVAL_MINUTES` near the top of `server.py`.

---

## Blog Series

Full writeups with setup instructions, screenshots, and explanations at **[n4mi.tech](https://n4mi.tech)**:

1. Stream Deck Basics — Mode Launchers & PowerShell Scripts
2. The Personal Operating Portal — Propagation Dashboard
3. Rotator Control from the Stream Deck
4. HamshackFeed — Lightweight Aggregator for ham radio blogs, podcasts and YouTube channels
5. Custom Icons, Getting Started & Closing Thoughts
6. HamShackFeedPro — Upgraded ham radio content aggregator
7. ManualShelf — A locally-hosted PDF and document catalog

---

## License

MIT License — free to use, modify, and share. If you adapt this for your own station, a mention of N4MI is appreciated but not required. 73!

---

*Developed with assistance from [Claude AI](https://claude.ai/) — Anthropic*
