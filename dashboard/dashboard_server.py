#!/usr/bin/env python3
"""
Ham Radio Dashboard Server
Serves the dashboard HTML and fetches DX spots via telnet cluster connection.
Save to: C:\Ham Scripts\dashboard_server.py
"""

import http.server
import urllib.request
import json
import os
import re
import socket
import time
from datetime import datetime, timezone

PORT     = 8073
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CALLSIGN = "N4MI"

# US-based telnet cluster nodes, tried in order
CLUSTER_NODES = [
    {"host": "dxc.wa9pie.net", "port": 8000},
    {"host": "k0xm.net",       "port": 7300},
    {"host": "w3lpl.net",      "port": 7373},
]

def freq_to_band(freq_khz):
    try:
        f = float(str(freq_khz).replace(",",""))
    except:
        return None
    if 3500  <= f < 4000:  return "80m"
    if 7000  <= f < 7300:  return "40m"
    if 14000 <= f < 14350: return "20m"
    if 18068 <= f < 18168: return "17m"
    if 21000 <= f < 21450: return "15m"
    if 24890 <= f < 24990: return "12m"
    if 28000 <= f < 29700: return "10m"
    if 50000 <= f < 54000: return "6m"
    return None

TARGET_BANDS = {"80m","40m","20m","17m","15m","12m","10m","6m"}

# Regex to parse standard DX cluster spot line:
# DX de W4ABC:     14195.0  PY2XB        599                        1423Z
SPOT_RE = re.compile(
    r"DX de\s+([\w\d/\-]+)[\s:]+(\d+\.?\d*)\s+([\w\d/\-]+)\s*(.*?)\s+(\d{4})Z",
    re.IGNORECASE
)

def fetch_spots_telnet():
    for node in CLUSTER_NODES:
        try:
            print(f"  Connecting to {node['host']}:{node['port']}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((node["host"], node["port"]))

            # Read initial banner and send callsign to log in
            time.sleep(1)
            banner = b""
            try:
                while True:
                    chunk = sock.recv(1024)
                    if not chunk: break
                    banner += chunk
                    if b"call" in banner.lower() or b"login" in banner.lower() or b">" in banner:
                        break
            except socket.timeout:
                pass

            # Log in with callsign
            sock.sendall((CALLSIGN + "\r\n").encode())
            time.sleep(1)

            # Request last 30 spots
            sock.sendall(b"sh/dx 30\r\n")
            time.sleep(2)

            # Read response
            data = b""
            sock.settimeout(5)
            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk: break
                    data += chunk
            except socket.timeout:
                pass

            sock.close()

            raw = data.decode("utf-8", errors="replace")
            spots = []

            for line in raw.splitlines():
                m = SPOT_RE.search(line)
                if m:
                    de, freq, dx, comment, t = m.groups()
                    band = freq_to_band(freq)
                    if band in TARGET_BANDS:
                        spots.append({
                            "band":    band,
                            "dx":      dx.strip(),
                            "freq":    freq.strip(),
                            "de":      de.strip(),
                            "comment": comment.strip()[:40],
                            "time":    t.strip() + "Z"
                        })

            if spots:
                print(f"  Got {len(spots)} spots from {node['host']}")
                return {"source": node["host"], "spots": spots, "error": None}
            else:
                print(f"  No spots parsed from {node['host']}, trying next...")

        except Exception as e:
            print(f"  {node['host']} failed: {e}")
            continue

    return {"source": None, "spots": [], "error": "All cluster nodes failed"}


class DashboardHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/spots":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC] Fetching DX spots via telnet...")
            result = fetch_spots_telnet()
            self.wfile.write(json.dumps(result).encode())
            return

        if self.path == "/api/solar":
            try:
                req = urllib.request.Request(
                    "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                    headers={"User-Agent": "N4MI-Dashboard/1.0"}
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # HamQSL XML proxy - fetches rich solar/band condition data server-side
        if self.path == "/api/hamqsl":
            try:
                req = urllib.request.Request(
                    "https://www.hamqsl.com/solarxml.php",
                    headers={"User-Agent": "N4MI-Dashboard/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    xml_data = resp.read().decode("utf-8", errors="replace")

                # Parse key fields from XML
                import re as _re
                def get_xml(tag, txt):
                    m = _re.search(r"<" + tag + r"[^>]*>(.*?)</" + tag + r">", txt, _re.DOTALL)
                    return m.group(1).strip() if m else ""

                result = {
                    "solarflux":    get_xml("solarflux", xml_data),
                    "aindex":       get_xml("aindex", xml_data),
                    "kindex":       get_xml("kindex", xml_data),
                    "sunspots":     get_xml("sunspots", xml_data),
                    "xray":         get_xml("xray", xml_data),
                    "protonflux":   get_xml("protonflux", xml_data),
                    "electonflux":  get_xml("electonflux", xml_data),
                    "aurora":       get_xml("aurora", xml_data),
                    "solarwind":    get_xml("solarwind", xml_data),
                    "magneticfield":get_xml("magneticfield", xml_data),
                    "geomagfield":  get_xml("geomagfield", xml_data),
                    "signalnoise":  get_xml("signalnoise", xml_data),
                    "fof2":         get_xml("fof2", xml_data),
                    "mufday":       get_xml("mufday", xml_data),
                    # Band conditions
                    "80m-40m":      get_xml("80m-40m", xml_data),
                    "30m-20m":      get_xml("30m-20m", xml_data),
                    "17m-15m":      get_xml("17m-15m", xml_data),
                    "12m-10m":      get_xml("12m-10m", xml_data),
                    "updated":      get_xml("updated", xml_data),
                    "source":       "hamqsl"
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                print(f"  HamQSL data fetched OK (SFI:{result['solarflux']} K:{result['kindex']})")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                print(f"  HamQSL fetch error: {e}")
            return

        super().do_GET()

    def log_message(self, format, *args):
        if "/api/" in str(args[0]):
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC] {args[0]}")


if __name__ == "__main__":
    os.chdir(SCRIPT_DIR)
    print(f"")
    print(f"  N4MI Ham Radio Dashboard Server")
    print(f"  Callsign:  {CALLSIGN}")
    print(f"  Dashboard: http://localhost:{PORT}/N4MI_PropagationDashboard.html")
    print(f"  Spots API: http://localhost:{PORT}/api/spots")
    print(f"")
    print(f"  Press Ctrl+C to stop.")
    print(f"")

    with http.server.ThreadingHTTPServer(("", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped. 73!")
