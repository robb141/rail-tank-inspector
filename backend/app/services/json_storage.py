import json
from pathlib import Path

from app.config import JSON_DIR, ensure_storage_dirs
from app.models import Inspection


def save_inspection_json(inspection: Inspection) -> Path:
    ensure_storage_dirs()
    safe_number = inspection.certificate_number.replace("/", "-").replace(" ", "_")
    path = JSON_DIR / f"inspection_{inspection.id}_{safe_number}.json"
    path.write_text(
        json.dumps(inspection.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
