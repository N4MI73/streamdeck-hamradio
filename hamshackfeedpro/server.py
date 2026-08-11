"""
server.py — HamShackFeed Pro
Flask server with SQLite persistence, direct RSS fetching, and scheduled refresh.
Run with: python server.py
Access at: http://localhost:8074  (or your local IP on port 8074)
"""

import os
import sqlite3
import threading
import webbrowser
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, abort
from apscheduler.schedulers.background import BackgroundScheduler
from fetcher import fetch_feed, detect_feed, get_feed_metadata

# ── Config ────────────────────────────────────────────────
PORT                     = 8074
REFRESH_INTERVAL_MINUTES = 30
DB_PATH                  = os.path.join(os.path.dirname(__file__), 'hamshackfeed.db')
YT_RSS                   = 'https://www.youtube.com/feeds/videos.xml?channel_id='

# ── Default sources (mirrors HamShackFeed) ────────────────
DEFAULT_SOURCES = [
    # Blogs
    {'name': 'DX World',        'type': 'blog',    'url': 'https://www.dx-world.net/feed/'},
    {'name': 'On All Bands',    'type': 'blog',    'url': 'https://www.onallbands.com/feed/'},
    {'name': 'KB6NU Blog',      'type': 'blog',    'url': 'https://www.kb6nu.com/feed/'},
    {'name': 'DX Zone',         'type': 'blog',    'url': 'https://www.dxzone.com/feed/'},
    {'name': 'DX News',         'type': 'blog',    'url': 'https://dxnews.com/feed/'},
    {'name': 'AR Newsline',     'type': 'blog',    'url': 'https://www.arnewsline.org/feed/'},
    {'name': 'This Week in AR', 'type': 'blog',    'url': 'https://twiar.net/feed/'},
    {'name': 'ARRL News',       'type': 'blog',    'url': 'https://www.arrl.org/arrl.rss'},
    # Podcasts
    {'name': 'Ham Radio Crash Course (Podcast)', 'type': 'podcast',
     'url': 'https://hamradiocrashcourse.podbean.com/feed.xml'},
    {'name': 'ARRL Roundtable', 'type': 'podcast', 'url': 'https://arroundtable.podbean.com/feed.xml'},
    {'name': 'Ham Radio Workbench', 'type': 'podcast', 'url': 'https://workbench.libsyn.com/rss'},
    {'name': 'ICQ Podcast',     'type': 'podcast', 'url': 'https://icqpodcast.libsyn.com/rss'},
    {'name': 'Ham Radio 2.0 (Podcast)', 'type': 'podcast',
     'url': 'https://www.spreaker.com/show/2042782/episodes/feed'},
    # YouTube
    {'name': 'Ham Radio Crash Course (YT)', 'type': 'youtube',
     'url': YT_RSS + 'UChAu6Cof9KlfFxSbL9ytosQ'},
    {'name': 'Ham Radio Concepts', 'type': 'youtube',
     'url': YT_RSS + 'UCuawHU2iYR_0tpYAIDyIH4Q'},
    {'name': 'Ham Radio 2.0 (YT)', 'type': 'youtube',
     'url': YT_RSS + 'UCKpVMjRE0m60lKCBWhIlo0A'},
    {'name': 'KM4ACK',          'type': 'youtube', 'url': YT_RSS + 'UCSQhXfGo_68Ta8-2wStAWkw'},
    {'name': 'Dave Casler',     'type': 'youtube', 'url': YT_RSS + 'UCaBtYooQdmNzq63eID8RaLQ'},
    {'name': 'Ham Nation',      'type': 'youtube', 'url': YT_RSS + 'UCBLgTMpPMkuV-xeEbx1UKZg'},
]

# ── Flask app ─────────────────────────────────────────────
app = Flask(__name__)

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS sources (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                type        TEXT    NOT NULL,
                url         TEXT    NOT NULL UNIQUE,
                home_url    TEXT,
                is_favorite INTEGER DEFAULT 0,
                is_default  INTEGER DEFAULT 0,
                last_fetched TEXT,
                last_error  TEXT,
                added_at    TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id   INTEGER NOT NULL,
                guid        TEXT    NOT NULL UNIQUE,
                title       TEXT,
                url         TEXT,
                description TEXT,
                thumbnail   TEXT,
                audio_url   TEXT,
                pub_date    TEXT,
                fetched_at  TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS read_items (
                guid    TEXT PRIMARY KEY,
                read_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_items_source  ON items(source_id);
            CREATE INDEX IF NOT EXISTS idx_items_pubdate ON items(pub_date DESC);
        ''')

        # Migration: add home_url to a sources table that already exists from before
        # this feature (CREATE TABLE IF NOT EXISTS above only affects brand-new installs).
        try:
            conn.execute('ALTER TABLE sources ADD COLUMN home_url TEXT')
        except sqlite3.OperationalError:
            pass  # column already exists

        # Seed defaults if table is empty
        count = conn.execute('SELECT COUNT(*) FROM sources').fetchone()[0]
        if count == 0:
            for src in DEFAULT_SOURCES:
                conn.execute(
                    'INSERT OR IGNORE INTO sources (name, type, url, is_default) VALUES (?,?,?,1)',
                    (src['name'], src['type'], src['url'])
                )

# ── Refresh logic ─────────────────────────────────────────
_refresh_lock   = threading.Lock()
_refreshing     = False
_last_refresh   = None
_next_refresh   = None

def refresh_all():
    global _refreshing, _last_refresh, _next_refresh
    if not _refresh_lock.acquire(blocking=False):
        return  # already running
    _refreshing = True
    try:
        with get_db() as conn:
            rows = conn.execute('SELECT * FROM sources').fetchall()
        sources = [dict(r) for r in rows]
        for src in sources:
            _refresh_source(src)
        _last_refresh = datetime.now().isoformat()
        _next_refresh = (datetime.now() + timedelta(minutes=REFRESH_INTERVAL_MINUTES)).isoformat()
    finally:
        _refreshing = False
        _refresh_lock.release()

def _refresh_source(source):
    items, error, home_url = fetch_feed(source)
    with get_db() as conn:
        if error:
            conn.execute(
                'UPDATE sources SET last_error=?, last_fetched=datetime("now") WHERE id=?',
                (str(error)[:500], source['id'])
            )
        else:
            if home_url:
                conn.execute(
                    'UPDATE sources SET last_error=NULL, last_fetched=datetime("now"), home_url=? WHERE id=?',
                    (home_url, source['id'])
                )
            else:
                conn.execute(
                    'UPDATE sources SET last_error=NULL, last_fetched=datetime("now") WHERE id=?',
                    (source['id'],)
                )
            for item in items:
                conn.execute('''
                    INSERT OR IGNORE INTO items
                        (source_id, guid, title, url, description, thumbnail, audio_url, pub_date)
                    VALUES
                        (:source_id, :guid, :title, :url, :description, :thumbnail, :audio_url, :pub_date)
                ''', item)

# ── Routes ─────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    with get_db() as conn:
        src_count  = conn.execute('SELECT COUNT(*) FROM sources').fetchone()[0]
        item_count = conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]
        read_count = conn.execute('SELECT COUNT(*) FROM read_items').fetchone()[0]
    return jsonify({
        'refreshing':               _refreshing,
        'last_refresh':             _last_refresh,
        'next_refresh':             _next_refresh,
        'refresh_interval_minutes': REFRESH_INTERVAL_MINUTES,
        'source_count':             src_count,
        'item_count':               item_count,
        'unread_count':             item_count - read_count,
    })


@app.route('/api/sources', methods=['GET'])
def api_sources_get():
    with get_db() as conn:
        rows = conn.execute('''
            SELECT s.*,
                   COUNT(i.id) as item_count,
                   SUM(CASE WHEN r.guid IS NULL THEN 1 ELSE 0 END) as unread_count
            FROM sources s
            LEFT JOIN items i      ON i.source_id = s.id
            LEFT JOIN read_items r ON r.guid = i.guid
            GROUP BY s.id
            ORDER BY LOWER(s.name)
        ''').fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/sources', methods=['POST'])
def api_sources_add():
    data     = request.get_json(force=True)
    raw_url  = (data.get('url') or '').strip()
    name     = (data.get('name') or '').strip()
    src_type = (data.get('type') or 'auto').strip()

    if not raw_url:
        return jsonify({'error': 'URL is required'}), 400

    # YouTube handle — can't auto-resolve
    if 'youtube.com/@' in raw_url or ('youtu.be' in raw_url and '@' in raw_url):
        return jsonify({'error':
            'YouTube handle URLs cannot be auto-resolved. '
            'Open the channel on YouTube, click About, and copy the channel URL '
            '(format: youtube.com/channel/UCxxxxxxx).'}), 400

    feed_url, detected_type = detect_feed(raw_url)
    if not feed_url:
        return jsonify({'error':
            'Could not find a valid RSS feed at that URL. '
            'Try appending /feed or /rss manually.'}), 400

    if src_type == 'auto':
        src_type = detected_type or 'blog'

    title, home_url = get_feed_metadata(feed_url)
    if not name:
        name = title or raw_url.split('/')[2].replace('www.', '')

    try:
        with get_db() as conn:
            cur = conn.execute(
                'INSERT INTO sources (name, type, url, home_url) VALUES (?,?,?,?)',
                (name, src_type, feed_url, home_url)
            )
            new_id = cur.lastrowid
            source = dict(conn.execute('SELECT * FROM sources WHERE id=?', (new_id,)).fetchone())
        # Fetch items immediately in background
        threading.Thread(target=_refresh_source, args=(source,), daemon=True).start()
        return jsonify(source), 201

    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': 'That source is already in your list'}), 409
        return jsonify({'error': str(e)}), 500


@app.route('/api/sources/<int:sid>', methods=['DELETE'])
def api_sources_delete(sid):
    with get_db() as conn:
        conn.execute('DELETE FROM sources WHERE id=?', (sid,))
    return '', 204


@app.route('/api/sources/<int:sid>/favorite', methods=['POST'])
def api_favorite_add(sid):
    with get_db() as conn:
        conn.execute('UPDATE sources SET is_favorite=1 WHERE id=?', (sid,))
    return jsonify({'is_favorite': True})


@app.route('/api/sources/<int:sid>/favorite', methods=['DELETE'])
def api_favorite_remove(sid):
    with get_db() as conn:
        conn.execute('UPDATE sources SET is_favorite=0 WHERE id=?', (sid,))
    return jsonify({'is_favorite': False})


@app.route('/api/items', methods=['GET'])
def api_items_get():
    source_id   = request.args.get('source')
    item_type   = request.args.get('type')
    unread_only = request.args.get('unread') == 'true'
    query       = (request.args.get('q') or '').strip()
    limit       = min(int(request.args.get('limit', 150)), 500)

    sql    = '''
        SELECT i.*,
               s.name  AS source_name,
               s.type  AS source_type,
               s.is_favorite,
               CASE WHEN r.guid IS NOT NULL THEN 1 ELSE 0 END AS is_read
        FROM items i
        JOIN  sources    s ON s.id   = i.source_id
        LEFT JOIN read_items r ON r.guid = i.guid
        WHERE 1=1
    '''
    params = []

    if source_id:
        sql += ' AND i.source_id = ?'; params.append(source_id)
    if item_type:
        sql += ' AND s.type = ?';       params.append(item_type)
    if unread_only:
        sql += ' AND r.guid IS NULL'
    if query:
        sql += ' AND (i.title LIKE ? OR i.description LIKE ? OR s.name LIKE ?)'
        params += [f'%{query}%', f'%{query}%', f'%{query}%']

    sql += ' ORDER BY i.pub_date DESC LIMIT ?'; params.append(limit)

    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/read', methods=['POST'])
def api_read_add():
    data  = request.get_json(force=True)
    guids = data.get('guids', [])
    if isinstance(guids, str):
        guids = [guids]
    with get_db() as conn:
        for g in guids:
            conn.execute('INSERT OR IGNORE INTO read_items (guid) VALUES (?)', (g,))
    return '', 204


@app.route('/api/read', methods=['DELETE'])
def api_read_remove():
    data  = request.get_json(force=True)
    guids = data.get('guids', [])
    if isinstance(guids, str):
        guids = [guids]
    with get_db() as conn:
        for g in guids:
            conn.execute('DELETE FROM read_items WHERE guid=?', (g,))
    return '', 204


@app.route('/api/read/all', methods=['POST'])
def api_read_all():
    with get_db() as conn:
        conn.execute('INSERT OR IGNORE INTO read_items (guid) SELECT guid FROM items')
    return '', 204


@app.route('/api/refresh', methods=['POST'])
def api_refresh_all():
    if _refreshing:
        return jsonify({'message': 'Refresh already in progress'}), 409
    threading.Thread(target=refresh_all, daemon=True).start()
    return jsonify({'message': 'Refresh started'})


@app.route('/api/refresh/<int:sid>', methods=['POST'])
def api_refresh_one(sid):
    with get_db() as conn:
        row = conn.execute('SELECT * FROM sources WHERE id=?', (sid,)).fetchone()
    if not row:
        abort(404)
    threading.Thread(target=_refresh_source, args=(dict(row),), daemon=True).start()
    return jsonify({'message': 'Refresh started'})


# ── Main ──────────────────────────────────────────────────
if __name__ == '__main__':
    print('─' * 52)
    print('  HamShackFeed Pro — starting up')
    print('─' * 52)

    init_db()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(refresh_all, 'interval',
                      minutes=REFRESH_INTERVAL_MINUTES, id='refresh_all')
    scheduler.start()

    # Initial fetch in background so server starts immediately
    threading.Thread(target=refresh_all, daemon=True).start()

    local_url = f'http://localhost:{PORT}'
    print(f'  Local:   {local_url}')
    print(f'  Network: http://<your-ip>:{PORT}')
    print(f'  Auto-refresh every {REFRESH_INTERVAL_MINUTES} minutes')
    print('─' * 52)

    # Open browser after a short delay
    threading.Timer(1.5, lambda: webbrowser.open(local_url)).start()

    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
