# PropMon
**Propagation & Tower Alert Backend** — N4MI | Dan Marshall

A small, always-on Docker service that fetches HF propagation and tower/weather safety data on a
timer, applies band-condition rating logic, and serves the result as flat JSON. No UI, no
persistence beyond an in-memory cache of the last successful fetch. Runs on the NAS, independent
of both shack computers, so consumers stay working even when the ham computer's own
`dashboard_server.py` is stopped. Port **8076**.

---

## Deploy (Portainer, Repository build method)

1. Stacks → Add stack → **Repository**
2. Repository URL: `https://github.com/N4MI73/streamdeck-hamradio`
3. Reference: `refs/heads/main`
4. **Compose path: `propmon/docker-compose.yml`** — this is a subfolder, not repo root
5. Environment variables: `TEMPEST_TOKEN` (see below)
6. GitOps auto-updates: off — update via manual "Pull and redeploy"
7. Deploy, then confirm via the health check endpoint

Python 3.12-slim base image. Dependencies (Flask, requests, astral) install automatically from
`requirements.txt` during the image build — nothing to install by hand.

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `TEMPEST_TOKEN` | Only for tower/weather alerts | WeatherFlow Tempest API token |

Set this in Portainer's stack environment config, never in the repo — it's read at runtime via
`os.environ` and deliberately excluded from the codebase. PropMon still runs and serves
propagation data without it; tower/weather alerts just stay at `NONE`.

---

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/instrument/propagation` | Main data endpoint |
| `GET /healthz` | Liveness check — `{"status": "ok"}` whenever the process is up, regardless of fetch/data state |

### Response shape

```json
{
  "updated": "2026-07-16T01:15:00Z",
  "summary": "GOOD: 160m 40m 30m | FAIR: 80m 20m 17m",
  "sfi": 100,
  "a_index": 14,
  "k_index": 1,
  "sunspots": 25,
  "xray": "C4.1",
  "solar_wind": 654.6,
  "bands": [
    {"band": "160m", "status": "good"},
    {"band": "80m",  "status": "fair"}
  ],
  "alerts": [
    {"category": "tower", "level": "NONE", "message": "No active alerts"}
  ],
  "tower_status": "NONE"
}
```

`alerts` is never an empty array in steady state — a calm system returns a single `NONE`-level
placeholder entry, not nothing, so a consumer never needs a special empty-array case.

---

## Data sources & refresh

| Data | Source | Refresh |
|---|---|---|
| SFI, sunspots, K/A-index, X-ray, solar wind | HamQSL XML (primary), NOAA SWPC K-index (fallback) | 5 min |
| Lightning, wind gust | WeatherFlow Tempest | 2 min |
| Severe weather alerts | NWS Alerts (zone-based) | 2 min |

On fetch failure, PropMon keeps serving the last successful result with its original timestamp
rather than erroring — a consumer can tell "service is down" (connection refused) apart from
"data is stale" (old `updated` timestamp).

---

## Band rating

10 bands (160m–6m), rated `good`/`fair`/`poor`. Score = `SFI × geomagnetic_penalty` (1.0× at K≤2,
0.65× at K≤4, 0.25× above that), compared against per-band, per-time-of-day thresholds.

Most bands use a fixed UTC-hour day/dawn/night/dusk clock. **160m and 80m are the exception** —
they compute real civil dusk/dawn for the station's coordinates (EM83) via the `astral` library
instead, since their day-vs-night thresholds are close to binary and a fixed clock's seasonal
drift against real sunset was producing impossible ratings on these two bands specifically (fixed
2026-07-16). If extending this service to new bands, watch for the same failure mode on any band
with a similarly steep day/night threshold jump.

Deliberately out of scope: atmospheric noise/QRN modeling (summer static on 160m/80m/40m).
PropMon's job is ionospheric band condition only.

---

## Related Projects

**[N4MI Propagation Monitor](https://github.com/N4MI73/n4mi-propagation-monitor)** — an
ESP32-based desktop hardware instrument (LilyGO T-Encoder Pro, round AMOLED display) that polls
this service's `/api/instrument/propagation` endpoint to drive a live propagation display. This is
PropMon's primary consumer today, but PropMon itself is general-purpose — anything that can make
an HTTP GET request can use this API. See that repo's own README for firmware setup and current
build status.

---

## File structure

```
propmon/
  propmon_server.py    Flask app, background fetch threads, band-rating logic
  Dockerfile            Python 3.12-slim, builds from requirements.txt
  docker-compose.yml    Portainer stack definition
  requirements.txt      flask, requests, astral
```
---

## Blog Post

This project is also described on my blog, n4mi.tech, in this article [PropMon – a Desktop Propagation Monitor](https://n4mi.tech/propmon-a-desktop-propagation-monitor/)

---
