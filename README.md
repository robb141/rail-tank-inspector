# Rail Inspect MVP

Offline-first railway tank inspection app, built incrementally.

This first version contains only the backend:

- FastAPI API
- Pydantic inspection model
- SQLite persistence
- JSON archive per submitted inspection
- DOCX certificate generation with `docxtpl`

Frontend PWA, IndexedDB offline storage, sync, PDF conversion, and Synology Docker deployment come later.

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

## Manual Document Reprint

The `Posledné záznamy` panel includes document buttons for saved inspections:

- `Použiť ako vzor` loads a saved inspection back into the form and saves it as
  the current draft.
- `Prvotný záznam` regenerates and downloads the checklist document.
- `Osvedčenie` appears only for passing inspections and regenerates/downloads
  the certificate.

This keeps printing manual for the MVP: open or download the DOCX, then print it
from Word/LibreOffice.

The `Offline fronta` panel also lets you:

- `Upraviť` a queued offline record by loading it back into the form and removing
  it from the queue.
- `Vymazať` a queued offline record before it syncs.

For tablet testing, open the site once while online, then use the browser's
install/add-to-home-screen action if available. On `localhost`, modern browsers
allow service workers for development.

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
POST /inspections
GET  /inspections
GET  /inspections/{inspection_id}
POST /inspections/{inspection_id}/certificate
POST /inspections/{inspection_id}/initial-record
```

## Next MVP Steps

1. Create placeholder DOCX templates from the real Slovak forms.
2. Add the basic tablet-friendly frontend form.
3. Store frontend submissions in IndexedDB while offline.
4. Add sync from tablet to backend when online.
5. Add PDF conversion with LibreOffice headless.
6. Package backend for Synology Container Manager with Docker.
