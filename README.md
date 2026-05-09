# Rail Inspect MVP

Vibe-coded offline-first railway tank inspection app, built incrementally.

This MVP currently includes:

- FastAPI API
- Pydantic inspection model
- SQLite persistence
- JSON archive per submitted inspection
- DOCX certificate generation with `docxtpl`
- PDF generation with LibreOffice headless
- Tablet-friendly PWA form
- IndexedDB draft/offline queue
- Docker setup for local/Synology deployment

## Project Structure

```text
railInspect/
  backend/
    app/
      db/
        sqlite.py
      services/
        documents.py
        json_storage.py
      templates/
        README.md
        osvedcenie_z_template.docx
        prvotny_zaznam_z_template.docx
      config.py
      main.py
      models.py
    data/
      generated/
      json/
      rail_inspections.sqlite3       # created automatically
    samples/
      inspection_payload.json
    requirements.txt
```

## Local Setup

Use Python 3.12 for this MVP. Python 3.14 can force packages such as
`pydantic-core` to build from source, which is the error you saw from
`maturin`.

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On macOS with Homebrew, install Python 3.12 if needed:

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 --version
```

If you already created `.venv` with Python 3.14 and saw a `pydantic-core`
`maturin` build error, recreate the environment with Python 3.12:

```bash
cd backend
mv .venv .venv-py314-failed
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Open the basic inspection form:

```text
http://127.0.0.1:8000
```

## Prepare The DOCX Templates

The starter templates were copied into:

```text
backend/app/templates/osvedcenie_z_template.docx
backend/app/templates/prvotny_zaznam_z_template.docx
```

The starter templates already contain the first MVP placeholders. The repeatable
script that inserted them is:

```bash
python3 scripts/update_template_placeholders.py
```

The current placeholders include:

```text
{{ certificate_number }}
{{ holder_name }}
{{ tank_identification }}
{{ tank_code }}
{{ test_pressure }}
{{ working_pressure }}
{{ inspection_place }}
{{ inspection_date }}
{{ next_inspection }}
{{ inspector_name }}
```

## Submit A Sample Inspection

```bash
curl -X POST http://127.0.0.1:8000/inspections \
  -H "Content-Type: application/json" \
  --data @samples/inspection_payload.json
```

You can also submit the same data from the browser form at:

```text
http://127.0.0.1:8000
```

## Offline Queue MVP

The browser form now has a small IndexedDB-backed offline queue and a PWA app
shell.

Basic behavior:

- If the backend is online, the form submits directly to `POST /inspections`.
- If the backend cannot be reached, the inspection is saved locally in the browser.
- Pending offline inspections appear in the `Offline fronta` panel.
- Click `Synchronizovať` after the backend is available again.
- The app also attempts to sync automatically when the browser reports that the
  network is online.
- The form UI is cached by a service worker, so the app shell can reopen while
  offline after the first successful visit.
- Form values are autosaved as a local draft while the inspector types.
- The draft is restored after refresh/reopen and cleared after successful submit
  or successful offline queue save.

To test it:

1. Open `http://127.0.0.1:8000`.
2. Stop Uvicorn with `Ctrl+C`.
3. Submit the form. It should appear in `Offline fronta`.
4. Restart Uvicorn.
5. Click `Synchronizovať`.

To test draft autosave, change a field, refresh the browser, and confirm the
edited value is restored.

## Checklist Fields

The tablet form and backend model now include the first expanded set of
`Prvotný záznam Z` checklist fields:

- inspection type and previous inspection references
- inspection result controls for exterior/interior/welds/plates/valves/gaskets
- safety valve type and number
- grounding, protocol numbers, wall thickness, measuring device, calibration,
  and test duration
- extraordinary inspection reason
- supplier measuring-device review fields

These fields are stored in SQLite/JSON and wired into the first pass of the
`Prvotný záznam Z` DOCX template.

## Manual Document Reprint

The `Posledné záznamy` panel includes document buttons for saved inspections:

- Search/filter controls let you narrow saved inspections by certificate number,
  tank ID, holder, place, date, inspector, and pass/fail result.
- `Použiť ako vzor` loads a saved inspection back into the form and saves it as
  the current draft.
- `Prvotný záznam` regenerates and downloads the checklist document.
- `Osvedčenie` appears only for passing inspections and regenerates/downloads
  the certificate.
- `Prvotný záznam PDF` and `Osvedčenie PDF` attempt to generate PDF versions
  using LibreOffice headless.

This keeps printing manual for the MVP: open or download the DOCX, then print it
from Word/LibreOffice.

PDF generation requires LibreOffice to be installed on the machine running the
backend. If LibreOffice is missing, the API returns a clear `503` response.
The Android tablet/browser does not need LibreOffice; it only uses the web app.
DOCX/PDF generation happens on the backend machine, such as your Mac, Windows PC,
NAS, or server.

On macOS, install LibreOffice manually or with Homebrew:

```bash
brew install --cask libreoffice
```

Then restart Uvicorn before trying the PDF buttons again.

If LibreOffice is installed but not on `PATH`, set `LIBREOFFICE_PATH` to the
`soffice` executable. Common examples:

```bash
export LIBREOFFICE_PATH="/Applications/LibreOffice.app/Contents/MacOS/soffice"
```

```powershell
$env:LIBREOFFICE_PATH = "C:\Program Files\LibreOffice\program\soffice.exe"
```

The `Offline fronta` panel also lets you:

- `Upraviť` a queued offline record by loading it back into the form and removing
  it from the queue.
- `Vymazať` a queued offline record before it syncs.

For tablet testing, open the site once while online, then use the browser's
install/add-to-home-screen action if available. On `localhost`, modern browsers
allow service workers for development.

If the browser appears to keep an older UI after code changes, refresh the page
once while the backend is running. The service worker now uses network-first
loading for the app shell and the CSS/JS URLs are versioned.

If `result` is `pass`, the backend also generates:

```text
backend/data/generated/osvedcenie_z_<id>_<certificate_number>.docx
```

For every submission, the backend generates:

```text
backend/data/generated/prvotny_zaznam_z_<id>_<certificate_number>.docx
```

Every submitted inspection is also saved as:

```text
backend/data/json/inspection_<id>_<certificate_number>.json
```

## Useful Endpoints

```text
GET  /health
GET  /health/pdf
POST /inspections
GET  /inspections
GET  /inspections/{inspection_id}
POST /inspections/{inspection_id}/certificate
POST /inspections/{inspection_id}/certificate/pdf
POST /inspections/{inspection_id}/initial-record
POST /inspections/{inspection_id}/initial-record/pdf
GET  /admin/export
POST /admin/import
```

## Backend Backup / Restore

Backend JSON export/import is available as API-only admin functionality.

Export all inspections:

```bash
curl http://127.0.0.1:8000/admin/export > rail-inspect-backup.json
```

Import a backup:

```bash
curl -X POST http://127.0.0.1:8000/admin/import \
  -H "Content-Type: application/json" \
  --data @rail-inspect-backup.json
```

Import skips duplicate inspections using:

```text
certificate_number + tank_identification + inspection_date
```

## Tests

The backend has a small pytest suite for the main MVP behavior:

- SQLite create, update, list, and import duplicate handling
- FastAPI create, update, read, export, and import endpoints
- certificate generation rules for failing inspections
- readable generated DOCX filenames

Install test dependencies:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run all tests:

```bash
pytest
```

Run one test file:

```bash
pytest tests/test_api.py
```

Run with more detail:

```bash
pytest -v
```

The tests use a temporary data folder created by pytest, so they do not touch
your real `backend/data/rail_inspections.sqlite3`, generated DOCX/PDF files, or
JSON archive.

From Docker, run tests inside a one-off container:

```bash
docker compose run --rm rail-inspect sh -c "pip install -r requirements-dev.txt && pytest"
```

## Docker

The MVP includes a simple Docker setup for local testing and later Synology
Container Manager deployment.

The Docker image includes LibreOffice Writer so PDF generation works inside the
container too. LibreOffice installed on your host computer is not visible inside
Docker unless it is installed in the image.

Build and run with Compose:

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:8000
```

Check PDF support inside the running container:

```text
http://127.0.0.1:8000/health/pdf
```

Stop:

```bash
docker compose down
```

The container stores persistent data in:

```text
backend/data/
```

That folder is mounted into the container as:

```text
/app/data
```

For Synology later, the same idea applies: mount a NAS folder to `/app/data` so
SQLite, generated JSON, and generated DOCX files survive container updates.

See [DEPLOYMENT.md](DEPLOYMENT.md) for local LAN and remote Tailscale deployment
flows.

## Synology Deployment Notes

Target layout on the NAS:

```text
/volume1/docker/rail-inspect/
  docker-compose.yml
  data/
```

Recommended volume mapping:

```text
/volume1/docker/rail-inspect/data  ->  /app/data
```

That `/app/data` folder contains:

```text
rail_inspections.sqlite3
json/
generated/
```

Basic deployment flow:

1. Copy the project or built image setup to Synology.
2. In Container Manager, create a project from `docker-compose.yml`.
3. Map host port `8000` to container port `8000`.
4. Mount the NAS data folder to `/app/data`.
5. Start the container.
6. Open the app from another device on the same LAN:

```text
http://NAS_IP_ADDRESS:8000
```

On the Android tablet:

1. Open the LAN URL once while online.
2. Use browser menu -> add to home screen / install app.
3. The PWA shell and IndexedDB offline queue work in the tablet browser.
4. DOCX/PDF generation still happens on the backend container, not on Android.

After deployment, check:

```text
http://NAS_IP_ADDRESS:8000/health
http://NAS_IP_ADDRESS:8000/health/pdf
```

For backup, export periodically:

```bash
curl http://NAS_IP_ADDRESS:8000/admin/export > rail-inspect-backup.json
```

Also back up the whole NAS data folder:

```text
/volume1/docker/rail-inspect/data
```

## Next MVP Steps

1. Add a full inspection detail view.
2. Improve DOCX/PDF layout after testing with real inspection data.
3. Add basic access protection before real LAN/NAS use.
