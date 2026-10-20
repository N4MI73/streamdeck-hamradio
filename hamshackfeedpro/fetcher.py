"""
fetcher.py — HamShackFeed Pro
Fetches and parses RSS/Atom feeds directly, no API proxy needed.
"""

import re
import hashlib
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit
import requests
import feedparser
from datetime import datetime

HEADERS = {
    'User-Agent': 'HamShackFeed Pro/1.0 (+https://github.com/N4MI73/streamdeck-hamradio)'
}
TIMEOUT = 15
YT_RSS  = 'https://www.youtube.com/feeds/videos.xml?channel_id='



# ── Outbound request safety (2026-10-20) ──────────────────────────────
# Feed URLs come from whoever adds a source, so HamShackFeed Pro only fetches
# public http(s) addresses: no loopback, private (LAN), link-local or other
# non-public destinations, checked again on every redirect hop. This stops
# the app being used to probe the NAS, router or other LAN services.
# (Limit: a DNS name that changes between the check and the request -- "DNS
# rebinding" -- isn't covered; acceptable for a LAN-only app.)
MAX_REDIRECTS = 5


class UnsafeURL(ValueError):
    pass


def check_public_url(url):
    """Raise UnsafeURL unless url is http(s) to a public address."""
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https'):
        raise UnsafeURL('Only http:// and https:// feed addresses are allowed')
    if parts.username or parts.password:
        raise UnsafeURL('Feed addresses with a user name or password are not allowed')
    host = parts.hostname
    if not host:
        raise UnsafeURL('Feed address has no host name')
    try:
        infos = socket.getaddrinfo(host, parts.port or (443 if parts.scheme == 'https' else 80),
                                   proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise UnsafeURL(f'Could not resolve {host}')
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split('%')[0])
        if not ip.is_global or ip.is_multicast:
            raise UnsafeURL(f'{host} is not a public internet address')


def safe_get(url, **kwargs):
    """requests.get that refuses non-public destinations, following up to
    MAX_REDIRECTS redirects itself so every hop is checked."""
    kwargs.setdefault('headers', HEADERS)
    kwargs.setdefault('timeout', TIMEOUT)
    for _ in range(MAX_REDIRECTS + 1):
        check_public_url(url)
        resp = requests.get(url, allow_redirects=False, **kwargs)
        if resp.is_redirect and resp.headers.get('location'):
            url = urljoin(url, resp.headers['location'])
            continue
        return resp
    raise UnsafeURL('Too many redirects')

def fetch_feed(source):
    """
    Fetch a feed source, return (list_of_items, error_string_or_None, home_url_or_None).
    home_url is the feed's declared site link (<link> at the channel/feed level, not
    per-entry) -- used to populate sources.home_url so source names can link out to the
    site itself rather than just individual items.
    """
    try:
        resp = safe_get(source['url'])
        resp.raise_for_status()
        d = feedparser.parse(resp.content)

        if not d.entries and d.bozo:
            return [], f"Parse error: {d.bozo_exception}", None

        home_url = (d.feed.get('link') or '').strip() or None

        items = []
        for entry in d.entries[:10]:
            item = _parse_entry(entry, source)
            if item:
                items.append(item)
        return items, None, home_url

    except requests.RequestException as e:
        return [], str(e), None
    except Exception as e:
        return [], str(e), None


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
            resp = safe_get(candidate)
            if resp.ok:
                d = feedparser.parse(resp.content)
                if d.entries:
                    return candidate, _sniff_type_from_feed(d)
        except Exception:
            continue

    # ── Try the URL itself as a feed ─────────────────────
    try:
        resp = safe_get(url)
        if resp.ok:
            d = feedparser.parse(resp.content)
            if d.entries:
                return url, _sniff_type_from_feed(d)
    except Exception:
        pass

    return None, None


def get_feed_metadata(feed_url):
    """
    Return (title_or_None, home_url_or_None) for a feed, in a single request.
    Used at add-source time -- home_url comes from the same parse as the title,
    no extra HTTP round-trip needed.
    """
    try:
        resp = safe_get(feed_url)
        d = feedparser.parse(resp.content)
        title = d.feed.get('title', '').strip()
        home_url = (d.feed.get('link') or '').strip()
        return (title or None, home_url or None)
    except Exception:
        return (None, None)


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
