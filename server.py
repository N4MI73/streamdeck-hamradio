"""
ManualShelf — PDF & Image Manual Catalog
N4MI | Dan Marshall | Grovetown GA

Flask server, port 8075
SQLite catalog: manualshelf.db
Thumbnails: static/thumbs/
Cross-computer: reads/writes manifest.json to NAS exchange folder
"""

import os, json, shutil, hashlib, datetime, threading, time, subprocess, platform
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
import sqlite3

# ── Config ───────────────────────────────────────────────────────────────────
PORT        = 8075
DB_PATH     = Path(__file__).parent / "manualshelf.db"
THUMB_DIR   = Path(__file__).parent / "static" / "thumbs"
CONFIG_FILE = Path(__file__).parent / "manualshelf_config.json"
THUMB_DIR.mkdir(parents=True, exist_ok=True)

# Supported file extensions
PDF_EXTS   = {".pdf"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
ALL_EXTS   = PDF_EXTS | IMAGE_EXTS

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Config helpers ────────────────────────────────────────────────────────────
def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {
        "scan_folders": [],
        "exchange_folder": "",
        "computer_name": platform.node(),
        "manifest_push": True,
        "manifest_pull": True,
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS manuals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash   TEXT UNIQUE NOT NULL,
                file_path   TEXT NOT NULL,
                filename    TEXT NOT NULL,
                title       TEXT NOT NULL,
                description TEXT DEFAULT '',
                file_type   TEXT NOT NULL,
                file_size   INTEGER DEFAULT 0,
                page_count  INTEGER DEFAULT 0,
                thumb_path  TEXT DEFAULT '',
                added_at    TEXT NOT NULL,
                tags        TEXT DEFAULT '',
                make        TEXT DEFAULT '',
                model       TEXT DEFAULT '',
                category    TEXT DEFAULT '',
                favorite    INTEGER DEFAULT 0,
                open_count  INTEGER DEFAULT 0,
                last_opened TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS scan_queue (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path   TEXT UNIQUE NOT NULL,
                filename    TEXT NOT NULL,
                file_type   TEXT NOT NULL,
                file_size   INTEGER DEFAULT 0,
                scanned_at  TEXT NOT NULL,
                in_catalog  INTEGER DEFAULT 0,
                is_updated  INTEGER DEFAULT 0
            );
        """)

init_db()

# ── Thumbnail generation ───────────────────────────────────────────────────────
def make_thumb_pdf(file_path: Path, hash_id: str) -> str:
    """Generate first-page thumbnail using PyMuPDF. Returns relative path or ''."""
    try:
        import fitz
        doc = fitz.open(str(file_path))
        page = doc[0]
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)
        out = THUMB_DIR / f"{hash_id}.jpg"
        pix.save(str(out))
        doc.close()
        return f"thumbs/{hash_id}.jpg"
    except Exception as e:
        print(f"Thumb error for {file_path}: {e}")
        return ""

def make_thumb_image(file_path: Path, hash_id: str) -> str:
    """Copy/resize image as thumbnail."""
    try:
        from PIL import Image
        img = Image.open(str(file_path))
        img.thumbnail((300, 400))
        out = THUMB_DIR / f"{hash_id}.jpg"
        img.convert("RGB").save(str(out), "JPEG", quality=85)
        return f"thumbs/{hash_id}.jpg"
    except Exception as e:
        print(f"Image thumb error for {file_path}: {e}")
        return ""

def file_hash(file_path: Path) -> str:
    h = hashlib.md5()
    h.update(str(file_path).encode())
    try:
        stat = file_path.stat()
        h.update(str(stat.st_size).encode())
        h.update(str(stat.st_mtime).encode())
    except:
        pass
    return h.hexdigest()[:16]

def get_page_count(file_path: Path) -> int:
    try:
        import fitz
        doc = fitz.open(str(file_path))
        n = len(doc)
        doc.close()
        return n
    except:
        return 0

# ── Folder scanning ────────────────────────────────────────────────────────────
def scan_folder(folder_path: str) -> list:
    """Scan a folder recursively, return list of discovered files."""
    results = []
    folder = Path(folder_path)
    if not folder.exists():
        return results
    for p in folder.rglob("*"):
        if p.suffix.lower() in ALL_EXTS and p.is_file():
            ext = p.suffix.lower()
            ft  = "pdf" if ext in PDF_EXTS else "image"
            results.append({
                "file_path": str(p),
                "filename":  p.name,
                "file_type": ft,
                "file_size": p.stat().st_size,
            })
    return results

# ── NAS Manifest ──────────────────────────────────────────────────────────────
def push_manifest():
    """Write this machine's catalog summary to the NAS exchange folder."""
    cfg = load_config()
    exc = cfg.get("exchange_folder", "").strip()
    if not exc or not cfg.get("manifest_push", True):
        return
    exc_path = Path(exc)
    if not exc_path.exists():
        try:
            exc_path.mkdir(parents=True)
        except:
            return
    computer = cfg.get("computer_name", platform.node())
    with get_db() as db:
        rows = db.execute(
            "SELECT filename, title, description, file_type, file_size, page_count, tags, make, model, category, added_at FROM manuals ORDER BY title"
        ).fetchall()
    manifest = {
        "computer":     computer,
        "updated":      datetime.datetime.now().isoformat(),
        "port":         PORT,
        "count":        len(rows),
        "manuals": [dict(r) for r in rows],
    }
    out = exc_path / f"manualshelf_{computer}.json"
    try:
        with open(out, "w") as f:
            json.dump(manifest, f, indent=2)
    except Exception as e:
        print(f"Manifest push error: {e}")

def pull_manifests():
    """Read other computers' manifests from the NAS exchange folder."""
    cfg = load_config()
    exc = cfg.get("exchange_folder", "").strip()
    computer = cfg.get("computer_name", platform.node())
    if not exc:
        return []
    exc_path = Path(exc)
    if not exc_path.exists():
        return []
    results = []
    for f in exc_path.glob("manualshelf_*.json"):
        if f.stem == f"manualshelf_{computer}":
            continue
        try:
            with open(f) as fh:
                data = json.load(fh)
            results.append(data)
        except:
            pass
    return results

# ── Background manifest push (every 5 min) ────────────────────────────────────
def manifest_loop():
    while True:
        time.sleep(300)
        try:
            push_manifest()
        except:
            pass

threading.Thread(target=manifest_loop, daemon=True).start()

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/thumbs/<path:filename>")
def serve_thumb(filename):
    return send_from_directory(THUMB_DIR, filename)

# --- Config ---

@app.route("/api/config", methods=["GET"])
def api_get_config():
    return jsonify(load_config())

@app.route("/api/config", methods=["POST"])
def api_save_config():
    cfg = load_config()
    data = request.json
    cfg.update(data)
    save_config(cfg)
    return jsonify({"ok": True})

# --- Scan ---

@app.route("/api/scan", methods=["POST"])
def api_scan():
    folder = (request.json or {}).get("folder", "").strip()
    if not folder or not Path(folder).exists():
        return jsonify({"error": "Folder not found"}), 400
    files = scan_folder(folder)

    with get_db() as db:
        # Build map of path -> stored_hash for everything currently in catalog
        existing = {
            r[0]: r[1]
            for r in db.execute("SELECT file_path, file_hash FROM manuals").fetchall()
        }
        now = datetime.datetime.now().isoformat()
        db.execute("DELETE FROM scan_queue")
        for f in files:
            p        = Path(f["file_path"])
            new_hash = file_hash(p)
            in_cat   = 1 if f["file_path"] in existing else 0
            # is_updated: path is known but the file has changed (new content/size/mtime)
            is_upd   = 1 if (f["file_path"] in existing and existing[f["file_path"]] != new_hash) else 0
            try:
                db.execute(
                    "INSERT OR REPLACE INTO scan_queue "
                    "(file_path,filename,file_type,file_size,scanned_at,in_catalog,is_updated) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (f["file_path"], f["filename"], f["file_type"], f["file_size"], now, in_cat, is_upd)
                )
            except:
                pass

    return jsonify({"found": len(files), "files": files})

@app.route("/api/scan_queue")
def api_scan_queue():
    with get_db() as db:
        rows = db.execute("SELECT * FROM scan_queue ORDER BY filename").fetchall()
    return jsonify([dict(r) for r in rows])

# --- Add to catalog ---

@app.route("/api/add", methods=["POST"])
def api_add():
    data = request.json or {}
    file_path = data.get("file_path", "").strip()
    if not file_path or not Path(file_path).exists():
        return jsonify({"error": "File not found"}), 400
    p   = Path(file_path)
    ext = p.suffix.lower()
    ft  = "pdf" if ext in PDF_EXTS else "image"
    hid = file_hash(p)
    now = datetime.datetime.now().isoformat()

    # Generate thumbnail
    if ft == "pdf":
        thumb = make_thumb_pdf(p, hid)
        pages = get_page_count(p)
    else:
        thumb = make_thumb_image(p, hid)
        pages = 0

    with get_db() as db:
        existing = db.execute(
            "SELECT id, title, description, tags, make, model, category, "
            "favorite, open_count, last_opened, thumb_path "
            "FROM manuals WHERE file_path=?", (str(p),)
        ).fetchone()

        if existing:
            # Same path, file has changed — refresh file data, preserve user metadata
            old_thumb = existing["thumb_path"]
            if old_thumb:
                old_tp = THUMB_DIR / Path(old_thumb).name
                old_tp.unlink(missing_ok=True)
            db.execute(
                "UPDATE manuals SET "
                "file_hash=?, filename=?, file_size=?, page_count=?, thumb_path=?, added_at=? "
                "WHERE id=?",
                (hid, p.name, p.stat().st_size, pages, thumb, now, existing["id"])
            )
            db.execute("UPDATE scan_queue SET in_catalog=1, is_updated=0 WHERE file_path=?", (str(p),))
            push_manifest()
            return jsonify({"ok": True, "id": existing["id"], "updated": True})

        # Brand-new entry
        title = p.stem.replace("_", " ").replace("-", " ")
        cur = db.execute(
            "INSERT OR IGNORE INTO manuals "
            "(file_hash,file_path,filename,title,description,file_type,file_size,"
            "page_count,thumb_path,added_at,tags,make,model,category) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (hid, str(p), p.name, title, data.get("description",""),
             ft, p.stat().st_size, pages, thumb, now,
             data.get("tags",""), data.get("make",""), data.get("model",""), data.get("category",""))
        )
        new_id = cur.lastrowid
        db.execute("UPDATE scan_queue SET in_catalog=1, is_updated=0 WHERE file_path=?", (str(p),))

    push_manifest()
    return jsonify({"ok": True, "id": new_id})

@app.route("/api/add_batch", methods=["POST"])
def api_add_batch():
    paths  = (request.json or {}).get("paths", [])
    added  = 0
    updated = 0
    errors = []
    now    = datetime.datetime.now().isoformat()

    for fp in paths:
        p = Path(fp)
        if not p.exists():
            errors.append(fp)
            continue
        ext = p.suffix.lower()
        ft  = "pdf" if ext in PDF_EXTS else "image"
        hid = file_hash(p)

        if ft == "pdf":
            thumb = make_thumb_pdf(p, hid)
            pages = get_page_count(p)
        else:
            thumb = make_thumb_image(p, hid)
            pages = 0

        try:
            with get_db() as db:
                existing = db.execute(
                    "SELECT id, thumb_path FROM manuals WHERE file_path=?", (str(p),)
                ).fetchone()

                if existing:
                    # Update: refresh file data, keep all user metadata intact
                    old_thumb = existing["thumb_path"]
                    if old_thumb:
                        old_tp = THUMB_DIR / Path(old_thumb).name
                        old_tp.unlink(missing_ok=True)
                    db.execute(
                        "UPDATE manuals SET "
                        "file_hash=?, filename=?, file_size=?, page_count=?, thumb_path=?, added_at=? "
                        "WHERE id=?",
                        (hid, p.name, p.stat().st_size, pages, thumb, now, existing["id"])
                    )
                    updated += 1
                else:
                    # New entry
                    title = p.stem.replace("_", " ").replace("-", " ")
                    db.execute(
                        "INSERT OR IGNORE INTO manuals "
                        "(file_hash,file_path,filename,title,description,file_type,file_size,"
                        "page_count,thumb_path,added_at,tags,make,model,category) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (hid, str(p), p.name, title, "", ft,
                         p.stat().st_size, pages, thumb, now, "", "", "", "")
                    )
                    added += 1

                db.execute(
                    "UPDATE scan_queue SET in_catalog=1, is_updated=0 WHERE file_path=?", (str(p),)
                )
        except Exception as e:
            errors.append(f"{fp}: {e}")

    push_manifest()
    return jsonify({"added": added, "updated": updated, "errors": errors})

# --- Catalog ---

@app.route("/api/manuals")
def api_manuals():
    q     = request.args.get("q", "").strip().lower()
    tag   = request.args.get("tag", "").strip().lower()
    cat   = request.args.get("category", "").strip()
    ft    = request.args.get("type", "").strip()
    fav   = request.args.get("favorite", "").strip()
    sort  = request.args.get("sort", "title")
    order = request.args.get("order", "asc")

    sort_col = {"title":"title","added":"added_at","name":"filename","opens":"open_count"}.get(sort,"title")
    ord_dir  = "DESC" if order == "desc" else "ASC"

    with get_db() as db:
        rows = db.execute(f"SELECT * FROM manuals ORDER BY {sort_col} {ord_dir}").fetchall()

    results = []
    for r in rows:
        d = dict(r)
        if q and q not in d["title"].lower() and q not in d["description"].lower() \
              and q not in (d["tags"] or "").lower() and q not in (d["make"] or "").lower() \
              and q not in (d["model"] or "").lower() and q not in d["filename"].lower():
            continue
        if tag and tag not in (d["tags"] or "").lower():
            continue
        if cat and cat != d.get("category",""):
            continue
        if ft and ft != d["file_type"]:
            continue
        if fav == "1" and not d["favorite"]:
            continue
        results.append(d)

    return jsonify(results)

@app.route("/api/manuals/<int:mid>", methods=["GET"])
def api_manual_get(mid):
    with get_db() as db:
        row = db.execute("SELECT * FROM manuals WHERE id=?", (mid,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))

@app.route("/api/manuals/<int:mid>", methods=["PATCH"])
def api_manual_update(mid):
    data = request.json or {}
    allowed = ["title","description","tags","make","model","category","favorite"]
    sets = ", ".join(f"{k}=?" for k in data if k in allowed)
    vals = [v for k,v in data.items() if k in allowed]
    if not sets:
        return jsonify({"ok": True})
    with get_db() as db:
        db.execute(f"UPDATE manuals SET {sets} WHERE id=?", vals + [mid])
    push_manifest()
    return jsonify({"ok": True})

@app.route("/api/manuals/<int:mid>", methods=["DELETE"])
def api_manual_delete(mid):
    with get_db() as db:
        row = db.execute("SELECT thumb_path FROM manuals WHERE id=?", (mid,)).fetchone()
        if row and row["thumb_path"]:
            tp = THUMB_DIR / Path(row["thumb_path"]).name
            if tp.exists():
                tp.unlink(missing_ok=True)
        db.execute("DELETE FROM manuals WHERE id=?\n", (mid,))
    push_manifest()
    return jsonify({"ok": True})

# --- Open file ---

@app.route("/api/open/<int:mid>", methods=["POST"])
def api_open(mid):
    with get_db() as db:
        row = db.execute("SELECT file_path FROM manuals WHERE id=?", (mid,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    fp = Path(row["file_path"])
    if not fp.exists():
        return jsonify({"error": f"File not found on disk: {fp}"}), 404
    try:
        if platform.system() == "Windows":
            os.startfile(str(fp))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(fp)])
        else:
            subprocess.Popen(["xdg-open", str(fp)])
        now = datetime.datetime.now().isoformat()
        with get_db() as db:
            db.execute("UPDATE manuals SET open_count=open_count+1, last_opened=? WHERE id=?", (now, mid))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Tags & categories ---

@app.route("/api/tags")
def api_tags():
    with get_db() as db:
        rows = db.execute("SELECT tags FROM manuals WHERE tags != ''").fetchall()
    tags = set()
    for r in rows:
        for t in r["tags"].split(","):
            t = t.strip()
            if t:
                tags.add(t)
    return jsonify(sorted(tags))

@app.route("/api/categories")
def api_categories():
    with get_db() as db:
        rows = db.execute("SELECT DISTINCT category FROM manuals WHERE category != '' ORDER BY category").fetchall()
    return jsonify([r["category"] for r in rows])

# --- Remote manifests ---

@app.route("/api/remote")
def api_remote():
    manifests = pull_manifests()
    return jsonify(manifests)

# --- Stats ---

@app.route("/api/stats")
def api_stats():
    with get_db() as db:
        total   = db.execute("SELECT COUNT(*) FROM manuals").fetchone()[0]
        pdfs    = db.execute("SELECT COUNT(*) FROM manuals WHERE file_type='pdf'").fetchone()[0]
        images  = db.execute("SELECT COUNT(*) FROM manuals WHERE file_type='image'").fetchone()[0]
        favs    = db.execute("SELECT COUNT(*) FROM manuals WHERE favorite=1").fetchone()[0]
        recents = db.execute("SELECT * FROM manuals WHERE last_opened!='' ORDER BY last_opened DESC LIMIT 5").fetchall()
    cfg = load_config()
    return jsonify({
        "total": total, "pdfs": pdfs, "images": images, "favorites": favs,
        "computer": cfg.get("computer_name", platform.node()),
        "recents": [dict(r) for r in recents],
    })

if __name__ == "__main__":
    print(f"ManualShelf starting on http://localhost:{PORT}")
    push_manifest()
    app.run(host="0.0.0.0", port=PORT, debug=False)
