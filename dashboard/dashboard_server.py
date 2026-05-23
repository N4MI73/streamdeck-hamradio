#!/usr/bin/env python3
"""
Ham Radio Dashboard Server - with Storm Alert Monitor
Save to: C:\Ham Scripts\dashboard_server.py

IMPORTANT: After sharing your token, regenerate it at:
  tempestwx.com -> Settings -> Data Authorizations
  Then update TEMPEST_TOKEN below with the new value.
"""

import http.server
import urllib.request
import json
import os
import re
import threading
import time
from datetime import datetime, timezone

PORT       = 8073
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Storm Alert Configuration ─────────────────────────────
TEMPEST_TOKEN      = "YOUR_TEMPEST_TOKEN_HERE"
TEMPEST_STATION_ID = "YOUR_STATION_ID"
NWS_ZONE           = "GAC073"   # Columbia County GA
CALLSIGN           = "N4MI"

# Alert poll intervals
NWS_POLL_SECONDS      = 120   # Check NWS every 2 minutes
TEMPEST_POLL_SECONDS  = 60    # Check Tempest every 1 minute

# Lightning thresholds
LIGHTNING_WARNING_KM  = 40    # Orange alert if lightning within 40km
LIGHTNING_CAUTION_KM  = 80    # Yellow caution if lightning within 80km
LIGHTNING_RECENT_MINS = 30    # Consider lightning "recent" if within 30 minutes

# Alert state shared across threads
alert_state = {
    "level":          "NONE",      # NONE, CAUTION, WARNING, CRITICAL
    "nws_alerts":     [],
    "lightning_km":   None,
    "lightning_ago":  None,
    "lightning_1hr":  0,
    "conditions":     "Unknown",
    "wind_gust":      None,
    "last_updated":   None,
    "error":          None,
}
alert_lock = threading.Lock()

# ── Tempest API polling ───────────────────────────────────
def fetch_tempest():
    url = (f"https://swd.weatherflow.com/swd/rest/better_forecast"
           f"?station_id={TEMPEST_STATION_ID}&token={TEMPEST_TOKEN}")
    req = urllib.request.Request(url, headers={"User-Agent": "N4MI-Dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def fetch_nws_alerts():
    url = f"https://api.weather.gov/alerts/active?zone={NWS_ZONE}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "N4MI-Dashboard/1.0 N4MI operator",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def alert_monitor_loop():
    """Background thread - polls Tempest and NWS, updates alert_state."""
    print("[STORM MONITOR] Starting alert monitor thread...")
    while True:
        try:
            now_utc = datetime.now(timezone.utc)

            # ── Fetch Tempest current conditions ─────────────
            try:
                tdata = fetch_tempest()
                cc = tdata.get("current_conditions", {})

                lightning_km   = cc.get("lightning_strike_last_distance")  # km
                lightning_epoch = cc.get("lightning_strike_last_epoch")     # unix timestamp
                lightning_1hr  = cc.get("lightning_strike_count_last_1hr", 0) or 0
                wind_gust      = cc.get("wind_gust")                        # m/s
                conditions     = cc.get("conditions", "Unknown")

                lightning_ago_min = None
                if lightning_epoch:
                    ago = (now_utc.timestamp() - lightning_epoch) / 60
                    lightning_ago_min = round(ago, 1)

            except Exception as e:
                print(f"[STORM MONITOR] Tempest error: {e}")
                lightning_km = lightning_ago_min = lightning_1hr = wind_gust = None
                conditions = "Error"

            # ── Fetch NWS alerts ─────────────────────────────
            try:
                nws_data = fetch_nws_alerts()
                features = nws_data.get("features", [])
                nws_alerts = []
                for f in features:
                    props = f.get("properties", {})
                    event    = props.get("event", "")
                    severity = props.get("severity", "")
                    headline = props.get("headline", "")
                    nws_alerts.append({
                        "event":    event,
                        "severity": severity,
                        "headline": headline[:120],
                    })
            except Exception as e:
                print(f"[STORM MONITOR] NWS error: {e}")
                nws_alerts = []

            # ── Determine alert level ─────────────────────────
            level = "NONE"

            # NWS critical alerts
            critical_events = [
                "Tornado Warning", "Tornado Emergency",
                "Severe Thunderstorm Warning", "Flash Flood Emergency"
            ]
            warning_events = [
                "Severe Thunderstorm Watch", "Tornado Watch",
                "Flash Flood Warning", "Flash Flood Watch"
            ]
            caution_events = [
                "Thunderstorm", "Special Weather Statement",
                "Dense Fog Advisory", "Wind Advisory"
            ]

            for alert in nws_alerts:
                ev = alert["event"]
                if any(c in ev for c in critical_events):
                    level = "CRITICAL"
                    break
                elif any(w in ev for w in warning_events) and level != "CRITICAL":
                    level = "WARNING"
                elif any(c in ev for c in caution_events) and level not in ("CRITICAL","WARNING"):
                    level = "CAUTION"

            # Lightning-based alerts (if no NWS critical alert already)
            if level != "CRITICAL":
                if (lightning_km is not None and lightning_ago_min is not None
                        and lightning_ago_min <= LIGHTNING_RECENT_MINS):
                    if lightning_km <= LIGHTNING_WARNING_KM:
                        if level != "WARNING":
                            level = "WARNING"
                    elif lightning_km <= LIGHTNING_CAUTION_KM:
                        if level == "NONE":
                            level = "CAUTION"

            # High wind gust caution (>15 m/s = ~35mph)
            if wind_gust and wind_gust >= 15 and level == "NONE":
                level = "CAUTION"

            # ── Update shared state ───────────────────────────
            with alert_lock:
                alert_state["level"]         = level
                alert_state["nws_alerts"]    = nws_alerts
                alert_state["lightning_km"]  = lightning_km
                alert_state["lightning_ago"] = lightning_ago_min
                alert_state["lightning_1hr"] = lightning_1hr
                alert_state["conditions"]    = conditions
                alert_state["wind_gust"]     = round(wind_gust * 2.237, 1) if wind_gust else None  # m/s to mph
                alert_state["last_updated"]  = now_utc.strftime("%H:%M UTC")
                alert_state["error"]         = None

            print(f"[STORM MONITOR] Level={level} | Lightning={lightning_km}km/{lightning_ago_min}min ago"
                  f" | NWS alerts={len(nws_alerts)} | Wind gust={wind_gust}")

        except Exception as e:
            print(f"[STORM MONITOR] Unexpected error: {e}")
            with alert_lock:
                alert_state["error"] = str(e)

        time.sleep(min(NWS_POLL_SECONDS, TEMPEST_POLL_SECONDS))


# ── HTTP request handler ──────────────────────────────────
class DashboardHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_GET(self):

        # Storm alert status endpoint
        if self.path == "/api/storm":
            with alert_lock:
                state_copy = dict(alert_state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(state_copy).encode())
            return

        # HamQSL solar XML proxy
        if self.path == "/api/hamqsl":
            try:
                req = urllib.request.Request(
                    "https://www.hamqsl.com/solarxml.php",
                    headers={"User-Agent": "N4MI-Dashboard/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    xml_data = resp.read().decode("utf-8", errors="replace")

                def get_xml(tag, txt):
                    m = re.search(r"<" + tag + r"[^>]*>(.*?)</" + tag + r">", txt, re.DOTALL)
                    return m.group(1).strip() if m else ""

                result = {
                    "solarflux":     get_xml("solarflux",    xml_data),
                    "aindex":        get_xml("aindex",       xml_data),
                    "kindex":        get_xml("kindex",       xml_data),
                    "sunspots":      get_xml("sunspots",     xml_data),
                    "xray":          get_xml("xray",         xml_data),
                    "protonflux":    get_xml("protonflux",   xml_data),
                    "aurora":        get_xml("aurora",       xml_data),
                    "solarwind":     get_xml("solarwind",    xml_data),
                    "magneticfield": get_xml("magneticfield",xml_data),
                    "geomagfield":   get_xml("geomagfield",  xml_data),
                    "signalnoise":   get_xml("signalnoise",  xml_data),
                    "updated":       get_xml("updated",      xml_data),
                    "source":        "hamqsl"
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # Serve static files
        super().do_GET()

    def log_message(self, format, *args):
        if "/api/" in str(args[0]):
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC] {args[0]}")


# ── Main ──────────────────────────────────────────────────
if __name__ == "__main__":
    os.chdir(SCRIPT_DIR)

    # Start alert monitor in background thread
    monitor_thread = threading.Thread(target=alert_monitor_loop, daemon=True)
    monitor_thread.start()

    print()
    print(f"  N4MI Ham Radio Dashboard Server")
    print(f"  Storm Monitor: ACTIVE (Tempest station {TEMPEST_STATION_ID})")
    print(f"  NWS Zone:      {NWS_ZONE} (Columbia County GA)")
    print(f"  Dashboard:     http://localhost:{PORT}/N4MI_PropagationDashboard.html")
    print(f"  Storm API:     http://localhost:{PORT}/api/storm")
    print()
    print(f"  REMINDER: Regenerate your Tempest token after this session!")
    print(f"  tempestwx.com -> Settings -> Data Authorizations")
    print()
    print(f"  Press Ctrl+C to stop.")
    print()

    with http.server.ThreadingHTTPServer(("", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped. 73!")
