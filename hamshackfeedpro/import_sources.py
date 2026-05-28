"""
import_sources.py — HamShackFeed Pro
Imports custom sources exported from HamShackFeed (HTML version) into HamShackFeed Pro.

Usage:
  1. Export sources from HamShackFeed.html browser console:
       const all = JSON.parse(localStorage.getItem('n4mi_sources_v2') || '[]');
       const custom = all.filter(s => String(s.id).startsWith('custom_'));
       copy(JSON.stringify(custom, null, 2));
  2. Paste clipboard contents into custom_sources.json in this folder.
  3. Make sure HamShackFeed Pro is running (python server.py).
  4. Run: python import_sources.py
"""

import json
import time
import sys
import os
import requests

SERVER   = 'http://localhost:8074'
JSON_FILE = os.path.join(os.path.dirname(__file__), 'custom_sources.json')

def main():
    # ── Load export file ──────────────────────────────────
    if not os.path.exists(JSON_FILE):
        print(f"ERROR: {JSON_FILE} not found.")
        print("Export your sources from the browser console first (see instructions at top of this file).")
        sys.exit(1)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        sources = json.load(f)

    if not sources:
        print("No sources found in custom_sources.json.")
        sys.exit(0)

    print(f"Found {len(sources)} source(s) to import.")

    # ── Check server is up ────────────────────────────────
    try:
        requests.get(f'{SERVER}/api/status', timeout=5)
    except requests.ConnectionError:
        print(f"ERROR: Cannot reach HamShackFeed Pro at {SERVER}")
        print("Make sure the server is running: python server.py")
        sys.exit(1)

    # ── Import each source ────────────────────────────────
    ok = skipped = failed = 0

    for src in sources:
        name = src.get('name', '')
        url  = src.get('url', '')
        typ  = src.get('type', 'blog')

        if not url:
            print(f"  SKIP  (no URL): {name}")
            skipped += 1
            continue

        try:
            r = requests.post(
                f'{SERVER}/api/sources',
                json={'url': url, 'name': name, 'type': typ},
                timeout=30
            )
            if r.status_code == 201:
                added_name = r.json().get('name', name)
                print(f"  OK    {added_name}")
                ok += 1
            elif r.status_code == 409:
                print(f"  SKIP  (already exists): {name}")
                skipped += 1
            else:
                err = r.json().get('error', r.text)
                print(f"  FAIL  {name}: {err}")
                failed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

        # Small delay between requests so the server isn't hammered
        time.sleep(0.5)

    # ── Summary ───────────────────────────────────────────
    print()
    print(f"Done — {ok} added, {skipped} skipped, {failed} failed")
    if ok:
        print(f"Open http://localhost:8074 to see your imported sources.")

if __name__ == '__main__':
    main()
