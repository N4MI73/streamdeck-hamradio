# ManualShelf
**PDF & Image Manual Catalog** — N4MI | Dan Marshall

A locally-hosted web app for cataloging and browsing radio manuals, accessory guides, and
settings screenshots. Runs on both the ham computer and admin computer. Port **8075**.

---

## Install

```powershell
cd "C:\Ham Scripts\manualshelf"
pip install -r requirements.txt
```

Requires Python 3.13 (Microsoft Store). PyMuPDF and Pillow are the only non-stdlib deps.

---

## Run

```powershell
# Start (opens browser automatically)
.\StartManualShelf.ps1

# Stop
.\StopManualShelf.ps1

# Or just run directly
python server.py
```

Then open http://localhost:8075

---

## First-time setup

1. Click **⚙ Settings** in the top bar
2. Set your **Computer Name** (e.g. `HamComputer` or `AdminComputer`)
3. If you want cross-computer visibility: set the **NAS Exchange Folder** (e.g. `Z:\Exchange\manualshelf`)
   and check both "Push" and "Pull"
4. Add your manual folders under **Saved Scan Folders**

---

## Adding manuals

1. Click **📂 Add Manuals**
2. Paste a folder path (e.g. `C:\Manuals\Radio`) and click **Scan**
3. Check the files you want to add, then click **Add Selected**
4. Files already in the catalog are grayed out and pre-excluded
5. Thumbnails are generated automatically from the first PDF page

---

## Features

- **Grid or list view** — toggle in toolbar
- **Search** — title, filename, make, model, description, tags
- **Tags** — comma-separated; browse via sidebar tag cloud
- **Categories** — filter by category (Transceiver, Software, etc.)
- **Favorites** — star key manuals
- **Open count** — tracks how often you open each file
- **Edit metadata** — title, make, model, category, description, tags in the detail panel
- **Remove from catalog** — does not delete the actual file
- **Sorts** — by title, date added, filename, most opened

---

## Cross-computer visibility

Each running instance writes a `manualshelf_<ComputerName>.json` manifest to the NAS
exchange folder every 5 minutes. The other machine reads it and shows remote manuals in
the **📡 Remote Manuals** sidebar filter.

Clicking a remote manual shows its metadata (title, make, model, description, tags, size).
It cannot be opened remotely — retrieve it via LocalSend or from the NAS exchange folder.

---

## File structure

```
C:\Ham Scripts\manualshelf\
  server.py               Flask app
  manualshelf.db          SQLite catalog
  manualshelf_config.json Settings
  requirements.txt
  StartManualShelf.ps1
  StopManualShelf.ps1
  static\
    thumbs\               Generated thumbnails (JPG)
  templates\
    index.html            UI
```

---

## Stream Deck button

**Action:** Open / Run  
**App:** `powershell.exe`  
**Arguments:** `-ExecutionPolicy Bypass -File "C:\Ham Scripts\manualshelf\StartManualShelf.ps1"`  
**Start In:** `C:\Ham Scripts\manualshelf`
