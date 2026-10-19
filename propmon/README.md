# PropMon has moved

PropMon's code now lives in the **[n4mi-shack-server](https://github.com/N4MI73/n4mi-shack-server/tree/main/propmon)**
repository, in its `propmon/` folder, with its full Git history. It moved on 2026-10-19.

- **Code, deploy steps, endpoints and the band-rating model:**
  [n4mi-shack-server/propmon/README.md](https://github.com/N4MI73/n4mi-shack-server/blob/main/propmon/README.md)
- **Image:** `ghcr.io/n4mi73/propmon`, built by GitHub Actions. Portainer pulls the image
  instead of building from source.
- **Nothing changed for consumers:** it still runs on the same host, on port 8076, at
  `/api/instrument/propagation`, with the same response shape.

Why: this repository now holds only services that run on a local Windows computer. Always-on
server software lives in n4mi-shack-server.

The old files are still in this repository's Git history (last version: commit `480601c`).
