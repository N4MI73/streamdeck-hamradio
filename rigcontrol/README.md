# rigcontrol — IC-7610 control from the Stream Deck

Band, mode, filter, ±100 kHz, split, preamp and NR/NB buttons for the **Icom IC-7610**,
sent over the radio's **LAN port** instead of its USB CI-V port. Your logger or WSJT-X keeps
the USB port exactly as before and simply follows the changes the buttons make.

Built and used daily at N4MI (N3FJP ACLog and WSJT-X sharing the 7610's USB port).
Like the rest of this repository, treat it as a working example to adapt, not a
turnkey product — see "Adapting it" below.

## How it works

```
Stream Deck button
   -> powershell.exe rig.ps1 <action>
       -> helper: rigplane serve  (127.0.0.1:4532, this computer only)
           -> IC-7610 LAN port    (UDP 50001-50003, logged in as Network User1)
```

- **The helper** is [rigplane](https://pypi.org/project/rigplane/) (an open-source Python
  library for Icom's LAN protocol) running its rigctld-compatible server. The first button
  press starts it hidden and logs into the radio (~5–10 s); after that every press is
  near-instant, because the helper stays logged in.
- **It listens on 127.0.0.1 only.** The helper can key the transmitter, so it is never
  exposed to the network.
- **Self-healing:** every press first asks the radio for its frequency. If the helper is
  missing or has stopped answering, the script restarts it.
- **Password:** `rig.ps1 setup` saves the radio's network user and password in
  `rig_cred.xml`, encrypted with Windows DPAPI (only the same Windows user on the same
  computer can read it). Never commit that file.
- **Log:** `rig.log` next to the script (rolls over at 200 KB). A failed press also plays
  the Windows error sound; the log says why.
- One action runs at a time; a second press waits for the first to finish.

## Buttons

| Button | Action | Result |
|---|---|---|
| 160 … 6 | `band 20` etc. | Saves the current frequency/mode/filter/data into the band you're leaving (band-stack register 1), then recalls the new band's register 1 — like the front-panel band key |
| SSB | `mode SSB` | LSB below 10 MHz (160/80/40 m), USB from 10 MHz up (60 m is USB); FIL2, data off. `mode USB` / `mode LSB` force a sideband |
| CW | `mode CW` | CW, FIL3 |
| USB-D1 | `mode DATA` | USB with DATA1, FIL1 (FT8/FT4) |
| FILTER | `filter` | FIL1 → FIL2 → FIL3 → FIL1; mode and data kept |
| +100k / −100k | `up` / `down` | Moves 100 kHz; stops at the US band edge (e.g. 14.350) instead of leaving the band |
| SPLIT UP 5 / UP 1 | `split SSB` / `split CW` | Copies MAIN to SUB, sets SUB 5 kHz (SSB) or 1 kHz (CW) above MAIN, split ON (you transmit on SUB). Refused if transmit would land above the US band edge |
| SPLIT OFF | `split OFF` | Split off |
| PREAMP | `preamp` | OFF → P.AMP1 → P.AMP2 → OFF |
| NR / NB | `nr` / `nb` | Toggle noise reduction / noise blanker |
| STOP | `stop` | Stops the helper and releases the radio's LAN session |
| — | `status` | Shows the helper state and what the radio is on (for testing) |
| — | `power OFF` | Radio off (not on a button; remote power-on proved unreliable and was left out) |

**Split safety:** band, mode and ±100k buttons turn split OFF first, so your transmit
frequency is never left on another band or in another mode.

60 m isn't included: the 7610 has no band-stacking register for it.

## Requirements

- Icom IC-7610 on your LAN (wired Ethernet), firmware with Network control
- Windows 10/11, Windows PowerShell 5.1 (built in) — PowerShell 7 also works
- Python 3.11 or newer
- Elgato Stream Deck with the **Advanced Launcher** plugin (or the built-in Open action)

## Setup

### 1. Radio

**MENU » SET » Network:**
- **Network Control: ON** — takes effect only after you power-cycle the radio
- **Network User1 ID** and **Password:** set them (Administrator = NO is fine)
- Note the radio's **IP address** (a DHCP reservation on your router keeps it fixed)

### 2. Files

```powershell
New-Item -ItemType Directory 'C:\Ham Scripts\rigcontrol' -Force | Out-Null
cd 'C:\Ham Scripts\rigcontrol'
# copy rig.ps1, README.md and the icons folder here, then:
python -m venv venv
.\venv\Scripts\python.exe -m pip install rigplane==2.11.1
```

Open `rig.ps1` in Notepad and set **`$RadioIP`** near the top to your radio's address.

### 3. Save the radio login and test

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\rig.ps1 setup
```

It asks for the Network User1 ID and password (the password is never shown), starts the
helper and prints what the radio is on. Then try a few actions from PowerShell before
building buttons:

```powershell
$r = { powershell.exe -ExecutionPolicy Bypass -File 'C:\Ham Scripts\rigcontrol\rig.ps1' @args }
& $r band 20
& $r mode CW
& $r filter
& $r split CW
& $r split OFF
```

### 4. Stream Deck buttons

Each button (Advanced Launcher):

- **Executable:** `powershell.exe`
- **Arguments:** `-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Ham Scripts\rigcontrol\rig.ps1" band 20`
  — replace `band 20` with the action from the table above
- **Start In:** anything; the script finds its own folder

> ⚠️ If you use `pwsh.exe` (PowerShell 7) instead, it must be the **MSI** install in
> `C:\Program Files\PowerShell\7\`. PowerShell 7 from the Microsoft Store or winget lives
> in a protected folder Stream Deck can't reach, and buttons fail silently.

N4MI's layout: a **RADIO** folder on the main page holds the ten band buttons, STOP and a
nested **MODES** folder (SSB, CW, USB-D1, FILTER, ±100k, the three split buttons, PREAMP,
NR, NB).

### 5. Icons

`icons/` holds 26 ready-made 144×144 icons and `make_icons.py`, the Pillow script that draws
them (`python make_icons.py` writes them to `icons/out/`). Change labels or colors there.

### 6. Stopping the helper

Press STOP, or add one line to your shutdown script (as `scripts/CloseHamRadio.ps1` does):

```powershell
& 'C:\Ham Scripts\rigcontrol\rig.ps1' stop
```

## Adapting it

- **Radio address and user:** `$RadioIP` at the top of `rig.ps1`; user and password via `setup`
- **Filters per mode button, split offsets, step size:** in `Invoke-ModeButton`,
  `Invoke-Split` and `$StepHz`
- **Band edges** (used by ±100k and split): the `Lo2`/`Hi2` values in the `$Bands` table — US
  allocations; change them for your country or licence class
- **Other Icom radios:** the CI-V commands come from the IC-7610 CI-V Reference Guide.
  Other LAN-capable Icoms (IC-705, IC-9700…) use a similar command set but different
  addresses (`98` in `$Civ`) and band codes — check your radio's CI-V guide and test each
  action before trusting it

## Things we learned (why the code looks the way it does)

- **Band-stack band codes are BCD:** 6 m is `0x10`, not `0x0A`. Codes 01–09 look the same
  either way, which hid the bug until the 6 m button.
- **rigplane 2.11.1 quirks:** a raw `26` write (mode + data + filter) or `25` write (SUB
  frequency) waits 2 s for a reply the radio never sends and holds up other commands, and
  its `M PKTUSB` mode command picks the wrong filter. The script uses `06` (mode + filter),
  `1A 06` (data mode + filter), and for split: copy MAIN to SUB (`07 B1`), select SUB
  (`07 D1`), set its frequency (`05`), select MAIN (`07 D0`), split on (`0F 01`).
- **A mode change can restore that mode's last filter** after applying yours, so the mode
  command is sent twice and checked by reading the mode back.
- **A CI-V band change doesn't save your spot** on the band you leave (the front-panel key
  does), so the script writes that register itself.
- **Pinned to rigplane 2.11.1** because that is what was tested. Before upgrading, test every
  button on the new version and keep the old `venv` until it passes.

## Files

| File | Purpose |
|---|---|
| `rig.ps1` | Everything: actions, helper start/stop, logging |
| `icons/*.png`, `icons/make_icons.py` | Button icons and the script that draws them |
| `rig_cred.xml` | *Created by setup — encrypted login; never commit* |
| `rig.log` | *Created at run time* |
| `venv\` | *Created at install — rigplane* |

73 de N4MI
