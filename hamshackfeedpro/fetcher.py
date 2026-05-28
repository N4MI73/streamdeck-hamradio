"""
fetcher.py — HamShackFeed Pro
Fetches and parses RSS/Atom feeds directly, no API proxy needed.
"""

import re
import hashlib
import requests
import feedparser
from datetime import datetime

HEADERS = {
    'User-Agent': 'HamShackFeed Pro/1.0 (+https://github.com/N4MI73/streamdeck-hamradio)'
}
TIMEOUT = 15
YT_RSS  = 'https://www.youtube.com/feeds/videos.xml?channel_id='


def fetch_feed(source):
    """
    Fetch a feed source, return (list_of_items, error_string_or_None).
    """
    try:
        resp = requests.get(source['url'], headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        d = feedparser.parse(resp.content)

        if not d.entries and d.bozo:
            return [], f"Parse error: {d.bozo_exception}"

        items = []
        for entry in d.entries[:10]:
            item = _parse_entry(entry, source)
            if item:
                items.append(item)
        return items, None

    except requests.RequestException as e:
        return [], str(e)
    except Exception as e:
        return [], str(e)


def _parse_entry(entry, source):
    """Convert a feedparser entry into a dict matching our DB schema."""

    # Stable GUID
    guid = entry.get('id') or entry.get('link') or ''
    if not guid:
        raw = f"{source['id']}:{entry.get('title', '')}"
        guid = hashlib.md5(raw.encode()).hexdigest()
    guid = guid[:500]

    # Publication date → ISO string
    pub_date = None
    for attr in ('published_parsed', 'updated_parsed'):
        t = getattr(entry, attr, None)
        if t:
            try:
                pub_date = datetime(*t[:6]).isoformat()
                break
            except Exception:
                pass

    # Thumbnail — YouTube media:thumbnail, then media_content, then enclosure image
    thumbnail = None
    if getattr(entry, 'media_thumbnail', None):
        thumbnail = entry.media_thumbnail[0].get('url')
    elif getattr(entry, 'media_content', None):
        for m in entry.media_content:
            if 'image' in m.get('type', '') or m.get('medium') == 'image':
                thumbnail = m.get('url')
                break
    if not thumbnail and getattr(entry, 'enclosures', None):
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                thumbnail = enc.get('href')
                break

    # Audio URL for podcasts
    audio_url = None
    if getattr(entry, 'enclosures', None):
        for enc in entry.enclosures:
            href = enc.get('href', '')
            mime = enc.get('type', '')
            if 'audio' in mime or href.lower().endswith(('.mp3', '.m4a', '.ogg', '.opus')):
                audio_url = href
                break

    # Description — strip HTML, cap at 300 chars
    description = ''
    for attr in ('summary', 'description', 'content'):
        val = getattr(entry, attr, None)
        if val:
            if isinstance(val, list):
                val = val[0].get('value', '') if val else ''
            description = re.sub(r'<[^>]+>', '', str(val)).strip()[:300]
            break

    return {
        'source_id':   source['id'],
        'guid':        guid,
        'title':       (entry.get('title') or 'Untitled')[:500],
        'url':         entry.get('link', ''),
        'description': description,
        'thumbnail':   thumbnail,
        'audio_url':   audio_url,
        'pub_date':    pub_date,
    }


def detect_feed(url):
    """
    Given a user-pasted URL, return (feed_url, type) or (None, None).
    type is one of: 'blog', 'podcast', 'youtube'
    """
    url = url.strip().rstrip('/')

    # ── YouTube ──────────────────────────────────────────
    yt_channel = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
    if yt_channel:
        return YT_RSS + yt_channel.group(1), 'youtube'

    # Handle-style YouTube URLs can't be resolved without the Data API.
    # Return the handle URL directly — feedparser may still parse it.
    if 'youtube.com/@' in url or 'youtu.be/' in url:
        return None, None   # caller should warn the user

    lower = url.lower()

    # ── Already a feed URL ───────────────────────────────
    already_feed = (
        re.search(r'\.(rss|xml|atom)(\?|$)', lower) or
        'feedburner.com' in lower or
        re.search(r'/feed/?(\?|$)', lower) or
        re.search(r'[?&]feed=', lower) or
        'libsyn.com/rss' in lower or
        lower.endswith('.rss')
    )
    if already_feed:
        src_type = _sniff_type(url)
        return url, src_type

    # ── Try common feed paths ────────────────────────────
    candidates = [
        url + '/feed',
        url + '/feed/',
        url + '/rss',
        url + '/rss.xml',
        url + '/atom.xml',
        url + '/index.xml',
    ]
    for candidate in candidates:
        try:
            resp = requests.get(candidate, headers=HEADERS, timeout=TIMEOUT)
            if resp.ok:
                d = feedparser.parse(resp.content)
                if d.entries:
                    return candidate, _sniff_type_from_feed(d)
        except Exception:
            continue

    # ── Try the URL itself as a feed ─────────────────────
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.ok:
            d = feedparser.parse(resp.content)
            if d.entries:
                return url, _sniff_type_from_feed(d)
    except Exception:
        pass

    return None, None


def get_feed_title(feed_url):
    """Return the feed's declared title, or None."""
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=TIMEOUT)
        d = feedparser.parse(resp.content)
        title = d.feed.get('title', '').strip()
        return title if title else None
    except Exception:
        return None


# ── Helpers ───────────────────────────────────────────────

def _sniff_type(url):
    """Guess type from URL alone."""
    lower = url.lower()
    if 'youtube.com' in lower:
        return 'youtube'
    if any(k in lower for k in ('podcast', 'podbean', 'spreaker', 'buzzsprout',
                                  'libsyn', 'audioboom', 'anchor', 'transistor')):
        return 'podcast'
    return 'blog'


def _sniff_type_from_feed(d):
    """Guess type from parsed feed content."""
    # Check for audio enclosures → podcast
    for entry in d.entries[:5]:
        if getattr(entry, 'enclosures', None):
            for enc in entry.enclosures:
                if 'audio' in enc.get('type', '') or \
                   enc.get('href', '').lower().endswith(('.mp3', '.m4a', '.ogg')):
                    return 'podcast'
    # Check for media thumbnails → youtube
    for entry in d.entries[:3]:
        if getattr(entry, 'media_thumbnail', None):
            return 'youtube'
    return 'blog'
