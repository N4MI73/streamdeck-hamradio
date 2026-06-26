# PropMon Service — Dockerfile
# Built by Portainer's "Repository" stack deployment method directly from
# github.com/N4MI73/streamdeck-hamradio — no local Docker build step needed
# on either Windows computer.

FROM python:3.12-slim

WORKDIR /app

# Only two real dependencies: Flask for the JSON endpoint, requests for
# the outbound HTTP calls to HamQSL/NOAA/Tempest/NWS.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY propmon_server.py .

EXPOSE 8076

CMD ["python", "propmon_server.py"]
