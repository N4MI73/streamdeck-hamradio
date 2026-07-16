# PropMon Service — Dockerfile
# Built by Portainer's "Repository" stack deployment method directly from
# github.com/N4MI73/streamdeck-hamradio — no local Docker build step needed
# on either Windows computer.

FROM python:3.12-slim

WORKDIR /app

# Flask for the JSON endpoint, requests for the outbound HTTP calls to
# HamQSL/NOAA/Tempest/NWS, astral for real sunrise/sunset/civil-twilight
# calculation (160m/80m day-night detection -- pure Python, no system deps).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY propmon_server.py .

EXPOSE 8076

CMD ["python", "propmon_server.py"]

