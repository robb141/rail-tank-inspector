# Rail Inspect Deployment

This app is designed so the tablet is only a browser/PWA, while the backend runs
on a server such as Synology NAS, Windows server, Mac, or Docker host.

## Recommended Architecture

```text
Android tablet / Windows laptop / Mac
  Browser or installed PWA
        |
        | LAN or Tailscale private network
        v
Synology / server
  Docker container
  FastAPI backend
  SQLite database
  DOCX/PDF generation with LibreOffice
        |
        v
Persistent data folder
  rail_inspections.sqlite3
  json/
  generated/
```

The tablet does not need Python, Docker, SQLite, Word, or LibreOffice.

## Mode 1: Local LAN

Use this when the inspector and Synology are on the same network.

### Synology Requirements

- Synology DSM
- Container Manager
- Rail Inspect Docker project
- A persistent data folder

Recommended folder:

```text
/volume1/docker/rail-inspect/data
```

Container volume mapping:

```text
/volume1/docker/rail-inspect/data -> /app/data
```

Port mapping:

```text
8000 -> 8000
```

### Tablet Setup

1. Connect tablet to the same Wi-Fi/LAN as Synology.
2. Open Chrome or Edge.
3. Open:

```text
http://SYNOLOGY_LAN_IP:8000
```

Example:

```text
http://192.168.1.50:8000
```

4. Use browser menu -> Add to Home screen / Install app.

## Mode 2: Remote Access With Tailscale

Use this when the inspector is outside the Synology network.

This is the recommended remote MVP approach because it avoids public port
forwarding.

### Install On Synology

1. Open Package Center.
2. Install Tailscale.
3. Sign in to the same Tailscale account/team.
4. Confirm Synology appears in the Tailscale admin console.
5. Note the Synology Tailscale IP address.

It usually looks like:

```text
100.x.y.z
```

### Install On Tablet

1. Install Tailscale from Google Play.
2. Sign in to the same Tailscale account/team.
3. Confirm the tablet is connected.
4. Open Chrome or Edge.
5. Open:

```text
http://SYNOLOGY_TAILSCALE_IP:8000
```

Example:

```text
http://100.88.12.34:8000
```

6. Add to Home screen / Install app.

## Full Remote Inspection Flow

1. Inspector opens Tailscale on tablet.
2. Inspector opens Rail Inspect PWA.
3. Inspector fills inspection form.
4. If connected:
   - tablet sends inspection to Synology backend
   - backend saves SQLite record
   - backend writes JSON archive
   - backend generates DOCX/PDF documents
5. If temporarily offline:
   - tablet saves inspection in IndexedDB offline queue
   - inspector syncs later with `Synchronizovať`
6. Inspector downloads/opens:
   - `Prvotný záznam`
   - `Osvedčenie`
   - PDF versions
7. Inspector prints manually from tablet, laptop, or office PC.

Printing does not need to happen on Synology. Synology generates the file; the
inspector prints it from the device that opens/downloads it.

## Docker Compose

Current `docker-compose.yml` maps:

```text
./backend/data -> /app/data
```

For Synology, adapt it to:

```yaml
volumes:
  - /volume1/docker/rail-inspect/data:/app/data
```

The app uses:

```yaml
environment:
  RAIL_INSPECT_DATA_DIR: /app/data
  LIBREOFFICE_PATH: /usr/bin/libreoffice
```

LibreOffice is installed inside the Docker image.

## Health Checks

Backend:

```text
http://SERVER_IP:8000/health
```

Expected:

```json
{"status":"ok"}
```

PDF support:

```text
http://SERVER_IP:8000/health/pdf
```

Expected:

```json
{
  "pdf_available": true,
  "libreoffice_path": "/usr/bin/libreoffice"
}
```

## Backup

Back up this folder:

```text
/volume1/docker/rail-inspect/data
```

It contains:

```text
rail_inspections.sqlite3
json/
generated/
```

Optional API export:

```bash
curl http://SERVER_IP:8000/admin/export > rail-inspect-backup.json
```

Restore/import:

```bash
curl -X POST http://SERVER_IP:8000/admin/import \
  -H "Content-Type: application/json" \
  --data @rail-inspect-backup.json
```

## Security Notes

For now, do not expose this app directly to the public internet.

Recommended MVP remote access:

```text
Tailscale only
```

Before using a public domain/reverse proxy, add:

- authentication
- HTTPS
- admin/user roles
- backup policy

## Troubleshooting

If the tablet cannot connect:

- confirm Tailscale is connected on tablet and Synology
- open `http://SYNOLOGY_TAILSCALE_IP:8000/health`
- confirm Docker container is running
- confirm port `8000` is mapped

If PDF generation fails:

- open `/health/pdf`
- confirm `pdf_available` is `true`
- rebuild Docker image if LibreOffice was added after the container was created

If offline sync does not work:

- confirm the tablet can open the app while online once
- check `Offline fronta`
- click `Synchronizovať`
- keep the app open until sync finishes
