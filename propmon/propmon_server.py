"""
PropMon Service — N4MI Desktop Instrument Series
==================================================

Small, always-on JSON data service for ESP32-based desktop instruments
(LilyGO T-Encoder Pro, starting with the Propagation Monitor).

Runs independently of dashboard_server.py (ham computer, port 8073) and of
any Windows computer being powered on at all — designed to live on the NAS
as a Docker container, so desktop instruments keep working even when the
ham shack dashboard server is intentionally stopped.

Data sources:
  - HamQSL XML feed (primary)      -> solar/band data
  - NOAA SWPC (fallback)           -> solar/band data, if HamQSL is down
  - WeatherFlow Tempest API        -> lightning/wind (tower alerts)
  - NWS Alerts API                 -> severe weather (tower alerts)

Behavior on fetch failure: keep serving the last known-good result with its
original "updated" timestamp, rather than erroring out. This lets firmware
tell the difference between "service is down" (connection refused) and
"data is stale" (old timestamp) -- two different, honestly-represented
failure modes.

No persistence. No database. Pure in-memory cache. Restarting this
container loses nothing except a few minutes of freshness until the next
fetch cycle completes.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from xml.etree import ElementTree

import requests
from astral import LocationInfo
from astral.sun import sun
from flask import Flask, jsonify

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HAMQSL_URL = "https://www.hamqsl.com/solarxml.php"
NOAA_KINDEX_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

# WeatherFlow Tempest -- station ID per project context (N4MI base context)
TEMPEST_STATION_ID = "159572"
TEMPEST_TOKEN = os.environ.get("TEMPEST_TOKEN", "")  # set via docker-compose.yml environment
TEMPEST_URL = "https://swd.weatherflow.com/swd/rest/better_forecast"

# NWS Alerts -- by zone (Columbia County GA), matching dashboard_server.py exactly,
# rather than a lat/lon point query.
NWS_ZONE = "GAC073"
NWS_ALERTS_URL = f"https://api.weather.gov/alerts/active?zone={NWS_ZONE}"
NWS_USER_AGENT = "N4MI-PropMon/1.0 N4MI operator"

# Lightning thresholds -- ported exactly from dashboard_server.py
LIGHTNING_WARNING_KM = 40    # WARNING if lightning within 40km
LIGHTNING_CAUTION_KM = 80    # CAUTION if lightning within 80km
LIGHTNING_RECENT_MINS = 30   # only counts if strike was within the last 30 min

# Wind gust threshold -- ported exactly from dashboard_server.py (m/s, ~35mph)
WIND_GUST_CAUTION_MPS = 15

SOLAR_FETCH_INTERVAL_SEC = 300   # 5 minutes
WEATHER_FETCH_INTERVAL_SEC = 120  # 2 minutes -- storm conditions change faster than solar data

# Data considered "stale" past this many minutes (firmware also checks this,
# this is just used server-side for logging/sanity, not enforced as an error)
STALE_THRESHOLD_MIN = 30

HTTP_TIMEOUT_SEC = 10

PORT = 8076

# EM83 station location -- used only for real sunrise/sunset/civil-twilight
# calculation (see LOW_BANDS section below). Approximate coordinates for
# Grovetown, GA. Not tied to the Tempest station or NWS zone configs above;
# those are separate identifiers for separate APIs describing the same
# physical location.
EM83_TZ = ZoneInfo("America/New_York")
EM83_LOCATION = LocationInfo("Grovetown", "USA", "America/New_York", 33.45, -82.19)

# ---------------------------------------------------------------------------
# Band rating thresholds
# ---------------------------------------------------------------------------
# Ported exactly from N4MI_PropagationDashboard.html's rateBand()/
# getTimeOfDay() JS (verbatim model, not re-derived). The dashboard's model
# is 8 bands (80m-6m). The PDF brief's worked example listed 10 bands
# including 160m and 30m, so per the brief we added 160m (below 80m's
# thresholds) and 30m (between 40m and 20m's thresholds), following the
# same pattern as neighboring bands. These two additions are new threshold
# tuning, not verbatim ports -- the *threshold numbers* were interpolated
# from neighboring bands, not the time-of-day logic itself.
#
# Model: geomagnetic penalty multiplies SFI itself (not a hard per-band
# K-index cutoff): kIdx<=2 -> 1.0x, kIdx<=4 -> 0.65x, else -> 0.25x.
# score = sfi * geo_penalty; band is "good" if score >= goodThresh,
# "fair" if score >= fairThresh, else "poor".
#
# --- 160m/80m time-of-day fix (2026-07-15/16) ---
# get_time_of_day() below uses fixed UTC-hour buckets, shared verbatim with
# the dashboard's JS. For most bands this is fine -- their day/dusk/night
# thresholds differ gradually, so a seasonal mismatch between the fixed
# clock and real sunset only nudges the rating slightly. 160m and 80m are
# different: both have a fully-closed "day" ([999, 999], impossible to
# reach) followed by a wide-open "night"/"dusk" threshold, a near-binary
# jump. Combined with the fixed clock's several-hour seasonal drift against
# real sunset (see propmon_160m_timeofday_issue.md), this produced a real
# bug: 160m rated GOOD during full daylight on 2026-07-15, 90+ minutes
# before actual sunset.
#
# Fix: 160m and 80m no longer use get_time_of_day()/the dusk+dawn buckets
# at all. They use get_low_band_tod() instead, which computes real civil
# dusk/dawn for EM83 (via the `astral` library) and returns a simple
# "day"/"night" state -- closed until it's genuinely dark, open once it
# is, confirmed against Dan's own on-air experience (160m/80m need to be
# genuinely dark, not just dusk, before they reliably open). Per Dan's
# direction, both bands share this identical logic rather than having
# separate offsets/ramps for each -- the difference between them wasn't
# judged large enough to justify separate models. Their "dawn"/"dusk"
# threshold entries below are removed since they're no longer looked up;
# only "day" and "night" are used for these two bands now.
#
# 30m was not reported as broken and is NOT touched by this fix -- it
# still uses the standard fixed-clock get_time_of_day(), same as the other
# 7 unaffected bands. Worth a look later per the original handoff note if
# it ever shows a similar symptom.
#
# Deliberately NOT included: any atmospheric-noise/QRN modeling for
# summer static on 160m/80m/40m. Dan already knows to expect that
# seasonally; PropMon's job is ionospheric band condition only.

BAND_ORDER = ["160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m"]

# Bands that use real sunrise/sunset (get_low_band_tod) instead of the
# fixed-clock get_time_of_day(). See fix notes above.
LOW_BANDS = {"160m", "80m"}

# { band: { tod: [fairThresh, goodThresh] } }
BAND_MODELS = {
    # 160m and 80m only use "day" and "night" now -- see fix notes above.
    # Threshold values themselves are unchanged from before the fix.
    "160m": {"day": [999, 999], "night": [60, 80]},
    "80m":  {"day": [999, 999], "night": [70, 90]},
    "40m":  {"night": [70, 90],  "dawn": [75, 95],   "day": [130, 160], "dusk": [75, 95]},
    # New addition (not in dashboard) -- interpolated between 40m and 20m's
    # thresholds at every time of day, following the same pattern as its
    # neighbors.
    "30m":  {"night": [82, 107], "dawn": [80, 102],  "day": [105, 132], "dusk": [80, 102]},
    "20m":  {"night": [95, 125], "dawn": [85, 110],  "day": [80, 105],  "dusk": [85, 110]},
    "17m":  {"night": [105, 135], "dawn": [95, 120],  "day": [90, 115],  "dusk": [95, 120]},
    "15m":  {"night": [120, 150], "dawn": [110, 140], "day": [105, 135], "dusk": [110, 140]},
    "12m":  {"night": [140, 170], "dawn": [130, 160], "day": [120, 150], "dusk": [130, 160]},
    "10m":  {"night": [155, 185], "dawn": [145, 175], "day": [130, 165], "dusk": [145, 175]},
    "6m":   {"night": [999, 999], "dawn": [160, 190], "day": [150, 185], "dusk": [160, 190]},
}


def get_geo_penalty(k_index: float) -> float:
    """Geomagnetic penalty multiplier on SFI, ported exactly from the
    dashboard's rateBand(): kIdx<=2 -> 1.0, kIdx<=4 -> 0.65, else -> 0.25."""
    if k_index <= 2:
        return 1.0
    elif k_index <= 4:
        return 0.65
    else:
        return 0.25

# EM83-tuned time-of-day boundaries (UTC hour) -- used for every band
# EXCEPT 160m and 80m (see get_low_band_tod below).
def get_time_of_day(utc_hour: int) -> str:
    """Mirrors dashboard_server.py's getTimeOfDay(): day 12-22 UTC,
    dusk 22-1, night 1-11, dawn 11-12."""
    if 12 <= utc_hour < 22:
        return "day"
    elif utc_hour >= 22 or utc_hour < 1:
        return "dusk"
    elif 1 <= utc_hour < 11:
        return "night"
    else:  # 11 <= utc_hour < 12
        return "dawn"


def get_low_band_tod(now_utc: datetime) -> str:
    """Real-sun-anchored day/night state for 160m and 80m, replacing the
    fixed-clock get_time_of_day() for these two bands only (see fix notes
    above BAND_MODELS). Returns "night" once civil dusk has ended for
    today's date in EM83 (Grovetown, GA), through to civil dawn the next
    morning; "day" otherwise.

    Civil dusk/dawn (sun 6 degrees below horizon) rather than sunset/
    sunrise themselves: cross-checked against Dan's own stated on-air
    experience (160m/80m need to be genuinely dark, not just dusk, before
    they reliably open) -- civil dusk end lines up with his reported
    "160m starts opening ~1800 EDT in winter, ~2100 EDT in summer" to
    within about 10 minutes at both extremes.

    Uses `astral` (pure-Python, no external API call) so this has no
    additional runtime dependency risk beyond the package itself.
    """
    local_now = now_utc.astimezone(EM83_TZ)
    s = sun(EM83_LOCATION.observer, date=local_now.date(), tzinfo=EM83_TZ)
    if local_now < s["dawn"] or local_now >= s["dusk"]:
        return "night"
    return "day"


def rate_band(sfi: float, k_index: float, band: str, tod: str) -> str:
    """Returns 'good', 'fair', or 'poor' for a given band at a given
    time-of-day, given current SFI and K-index. Ported exactly from the
    dashboard's rateBand(): geomagnetic penalty multiplies SFI into a
    single score, compared against the band's fair/good thresholds."""
    fair_thresh, good_thresh = BAND_MODELS[band][tod]
    geo = get_geo_penalty(k_index)
    score = sfi * geo

    if score >= good_thresh:
        return "good"
    elif score >= fair_thresh:
        return "fair"
    else:
        return "poor"


# ---------------------------------------------------------------------------
# Shared in-memory cache
# ---------------------------------------------------------------------------

_cache_lock = threading.Lock()
_cache = {
    "solar": {
        "updated": None,
        "sfi": None,
        "a_index": None,
        "k_index": None,
        "sunspots": None,
        "xray": None,
        "solar_wind": None,
    },
    "tower_status": "NONE",
    "alerts": [],
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("propmon")


# ---------------------------------------------------------------------------
# Solar / band data fetch (HamQSL primary, NOAA fallback)
# ---------------------------------------------------------------------------

def fetch_hamqsl():
    """Fetch and parse HamQSL's solarxml.php feed. Returns a dict of solar
    values, or None on failure."""
    resp = requests.get(HAMQSL_URL, timeout=HTTP_TIMEOUT_SEC)
    resp.raise_for_status()
    root = ElementTree.fromstring(resp.content)

    solardata = root.find("solardata")
    if solardata is None:
        raise ValueError("HamQSL response missing <solardata>")

    def _text(tag, cast=str, default=None):
        el = solardata.find(tag)
        if el is None or el.text is None:
            return default
        try:
            return cast(el.text.strip())
        except (ValueError, TypeError):
            return default

    return {
        "sfi": _text("solarflux", int),
        "a_index": _text("aindex", int),
        "k_index": _text("kindex", int),
        "sunspots": _text("sunspots", int),
        "xray": _text("xray", str),
        "solar_wind": _text("solarwind", float),
    }


def fetch_noaa_fallback():
    """Fallback solar data source -- NOAA SWPC planetary K-index.
    Much sparser than HamQSL; only fills in k_index. Used only if HamQSL
    is unreachable."""
    resp = requests.get(NOAA_KINDEX_URL, timeout=HTTP_TIMEOUT_SEC)
    resp.raise_for_status()
    data = resp.json()
    # First row is headers; take the most recent data row.
    if len(data) < 2:
        raise ValueError("NOAA k-index response had no data rows")
    last_row = data[-1]
    k_index = int(float(last_row[1]))
    return {
        "sfi": None,
        "a_index": None,
        "k_index": k_index,
        "sunspots": None,
        "xray": None,
        "solar_wind": None,
    }


def build_bands_and_summary(solar: dict):
    """Computes per-band ratings and a short human-readable summary string,
    given current SFI/K-index. The summary mirrors the dashboard HTML's own
    statusRow grouping (e.g. "GOOD: 20m 17m") rather than picking one
    arbitrary 'best' band -- the dashboard itself never reduces this to a
    single band, so neither does PropMon."""
    sfi = solar.get("sfi")
    k_index = solar.get("k_index")

    if sfi is None or k_index is None:
        # Not enough data to rate bands meaningfully.
        bands = [{"band": b, "status": "poor"} for b in BAND_ORDER]
        return bands, "Data unavailable"

    now_utc = datetime.now(timezone.utc)
    standard_tod = get_time_of_day(now_utc.hour)
    low_band_tod = get_low_band_tod(now_utc)

    bands = []
    for b in BAND_ORDER:
        tod = low_band_tod if b in LOW_BANDS else standard_tod
        bands.append({"band": b, "status": rate_band(sfi, k_index, b, tod)})

    groups = {"good": [], "fair": [], "poor": []}
    for b in bands:
        groups[b["status"]].append(b["band"])

    parts = []
    for level in ("good", "fair"):  # poor bands aren't worth calling out in the summary
        if groups[level]:
            parts.append(f"{level.upper()}: {' '.join(groups[level])}")
    summary = " | ".join(parts) if parts else "POOR: all bands"

    return bands, summary


def solar_fetch_loop():
    """Background thread: refreshes solar/band data every
    SOLAR_FETCH_INTERVAL_SEC seconds, forever."""
    while True:
        try:
            solar = fetch_hamqsl()
            log.info("HamQSL fetch OK: SFI=%s K=%s", solar.get("sfi"), solar.get("k_index"))
        except Exception as e:
            log.warning("HamQSL fetch failed (%s), trying NOAA fallback", e)
            try:
                solar = fetch_noaa_fallback()
                log.info("NOAA fallback fetch OK: K=%s", solar.get("k_index"))
            except Exception as e2:
                log.error("NOAA fallback also failed (%s) -- keeping last known-good data", e2)
                solar = None

        if solar is not None:
            bands, summary = build_bands_and_summary(solar)
            with _cache_lock:
                _cache["solar"] = {
                    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "sfi": solar.get("sfi"),
                    "a_index": solar.get("a_index"),
                    "k_index": solar.get("k_index"),
                    "sunspots": solar.get("sunspots"),
                    "xray": solar.get("xray"),
                    "solar_wind": solar.get("solar_wind"),
                    "bands": bands,
                    "summary": summary,
                }
        # else: leave _cache["solar"] untouched -- last known-good data
        # (with its original timestamp) keeps being served.

        time.sleep(SOLAR_FETCH_INTERVAL_SEC)


# ---------------------------------------------------------------------------
# Tower / weather alert fetch (Tempest + NWS)
# ---------------------------------------------------------------------------

def fetch_tempest():
    """Fetch current conditions from WeatherFlow Tempest station, via the
    same better_forecast endpoint dashboard_server.py uses. Returns a dict
    with lightning distance/age/1hr-count and wind gust (in mph), or raises
    on failure."""
    if not TEMPEST_TOKEN:
        raise RuntimeError("TEMPEST_TOKEN not configured")

    url = f"{TEMPEST_URL}?station_id={TEMPEST_STATION_ID}&token={TEMPEST_TOKEN}"
    resp = requests.get(url, headers={"User-Agent": "N4MI-PropMon/1.0"}, timeout=HTTP_TIMEOUT_SEC)
    resp.raise_for_status()
    data = resp.json()

    cc = data.get("current_conditions", {})
    lightning_km = cc.get("lightning_strike_last_distance")
    lightning_epoch = cc.get("lightning_strike_last_epoch")
    lightning_1hr = cc.get("lightning_strike_count_last_1hr", 0) or 0
    wind_gust_mps = cc.get("wind_gust")  # Tempest reports m/s

    lightning_ago_min = None
    if lightning_epoch:
        now_utc = datetime.now(timezone.utc).timestamp()
        lightning_ago_min = round((now_utc - lightning_epoch) / 60, 1)

    return {
        "lightning_km": lightning_km,
        "lightning_ago_min": lightning_ago_min,
        "lightning_1hr": lightning_1hr,
        "wind_gust_mph": round(wind_gust_mps * 2.237, 1) if wind_gust_mps else None,
        "wind_gust_mps": wind_gust_mps,
    }


def fetch_nws_alerts():
    """Fetch active NWS alerts for the configured zone (Columbia County GA),
    matching dashboard_server.py exactly. Returns a list of dicts with
    event/severity/headline."""
    resp = requests.get(
        NWS_ALERTS_URL,
        headers={"User-Agent": NWS_USER_AGENT, "Accept": "application/json"},
        timeout=HTTP_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    data = resp.json()
    alerts = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        alerts.append({
            "event": props.get("event", ""),
            "severity": props.get("severity", ""),
            "headline": props.get("headline", "")[:120],
        })
    return alerts


# NWS event-name matching, ported exactly from dashboard_server.py
CRITICAL_EVENTS = [
    "Tornado Warning", "Tornado Emergency",
    "Severe Thunderstorm Warning", "Flash Flood Emergency",
]
WARNING_EVENTS = [
    "Severe Thunderstorm Watch", "Tornado Watch",
    "Flash Flood Warning", "Flash Flood Watch",
]
CAUTION_EVENTS = [
    "Thunderstorm", "Special Weather Statement",
    "Dense Fog Advisory", "Wind Advisory",
]


def classify_tower_status(tempest: dict | None, nws_alerts: list) -> tuple[str, list]:
    """Combines Tempest readings + NWS alerts into a tower_status level
    (NONE/CAUTION/WARNING/CRITICAL) and a list of category-tagged alert
    dicts for the firmware. Logic ported exactly from dashboard_server.py's
    alert_monitor_loop -- same event-name matching, same lightning distance/
    recency thresholds, same wind gust threshold."""
    level = "NONE"
    alerts = []

    for alert in nws_alerts:
        ev = alert["event"]
        if any(c in ev for c in CRITICAL_EVENTS):
            level = "CRITICAL"
        elif any(w in ev for w in WARNING_EVENTS) and level != "CRITICAL":
            level = "WARNING"
        elif any(c in ev for c in CAUTION_EVENTS) and level not in ("CRITICAL", "WARNING"):
            level = "CAUTION"

        if level != "NONE":
            alerts.append({
                "category": "tower",
                "level": level,
                "message": alert.get("headline") or alert.get("event", "Weather alert"),
            })

    if tempest:
        lightning_km = tempest.get("lightning_km")
        lightning_ago_min = tempest.get("lightning_ago_min")
        lightning_1hr = tempest.get("lightning_1hr") or 0

        if level != "CRITICAL":
            if (lightning_km is not None and lightning_ago_min is not None
                    and lightning_ago_min <= LIGHTNING_RECENT_MINS):
                if lightning_km <= LIGHTNING_WARNING_KM:
                    if level != "WARNING":
                        level = "WARNING"
                    alerts.append({
                        "category": "tower",
                        "level": "WARNING",
                        "message": f"Lightning {lightning_km}km, {lightning_1hr} strikes/hr",
                    })
                elif lightning_km <= LIGHTNING_CAUTION_KM:
                    if level == "NONE":
                        level = "CAUTION"
                    alerts.append({
                        "category": "tower",
                        "level": "CAUTION",
                        "message": f"Lightning {lightning_km}km, {lightning_1hr} strikes/hr",
                    })

        wind_gust_mps = tempest.get("wind_gust_mps")
        if wind_gust_mps and wind_gust_mps >= WIND_GUST_CAUTION_MPS and level == "NONE":
            level = "CAUTION"
            alerts.append({
                "category": "tower",
                "level": "CAUTION",
                "message": f"Wind gust {tempest.get('wind_gust_mph')} mph",
            })

    if not alerts:
        alerts.append({"category": "tower", "level": "NONE", "message": "No active alerts"})

    return level, alerts


def weather_fetch_loop():
    """Background thread: refreshes tower/weather alerts every
    WEATHER_FETCH_INTERVAL_SEC seconds, forever. Mirrors
    dashboard_server.py's alert_monitor_loop polling pattern, but runs
    independently against the same two data sources."""
    while True:
        tempest = None
        nws_alerts = []
        any_success = False

        try:
            tempest = fetch_tempest()
            any_success = True
        except Exception as e:
            log.warning("Tempest fetch failed: %s", e)

        try:
            nws_alerts = fetch_nws_alerts()
            any_success = True
        except Exception as e:
            log.warning("NWS alerts fetch failed: %s", e)

        if any_success:
            tower_status, tower_alerts = classify_tower_status(tempest, nws_alerts)
            with _cache_lock:
                existing_propagation_alerts = [
                    a for a in _cache["alerts"] if a.get("category") == "propagation"
                ]
                _cache["alerts"] = existing_propagation_alerts + tower_alerts
                _cache["tower_status"] = tower_status
            log.info("Weather fetch OK: tower_status=%s", tower_status)
        # else: leave _cache["alerts"]/["tower_status"] untouched -- keep
        # last known-good tower data rather than wiping it on a transient
        # outage of both sources.

        time.sleep(WEATHER_FETCH_INTERVAL_SEC)


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.route("/api/instrument/propagation", methods=["GET"])
def propagation_endpoint():
    with _cache_lock:
        solar = _cache["solar"]
        if solar.get("updated") is None:
            # No successful fetch yet since startup.
            return jsonify({"error": "no_data_yet"}), 503

        payload = {
            "updated": solar["updated"],
            "summary": solar.get("summary", "Unknown"),
            "sfi": solar.get("sfi"),
            "a_index": solar.get("a_index"),
            "k_index": solar.get("k_index"),
            "sunspots": solar.get("sunspots"),
            "xray": solar.get("xray"),
            "solar_wind": solar.get("solar_wind"),
            "bands": solar.get("bands", []),
            "alerts": _cache["alerts"],
            "tower_status": _cache["tower_status"],
        }
    return jsonify(payload)


@app.route("/healthz", methods=["GET"])
def health_check():
    """Simple liveness check -- distinct from data freshness. Returns 200
    as long as the Flask process is up, regardless of fetch success."""
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    solar_thread = threading.Thread(target=solar_fetch_loop, daemon=True)
    weather_thread = threading.Thread(target=weather_fetch_loop, daemon=True)
    solar_thread.start()
    weather_thread.start()

    log.info("PropMon starting on port %d", PORT)
    app.run(host="0.0.0.0", port=PORT)
