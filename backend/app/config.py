import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("RAIL_INSPECT_DATA_DIR", BASE_DIR / "data"))
JSON_DIR = DATA_DIR / "json"
GENERATED_DIR = DATA_DIR / "generated"
DB_PATH = DATA_DIR / "rail_inspections.sqlite3"
LOOKUPS_XLSX_PATH = Path(os.getenv("RAIL_INSPECT_LOOKUPS_XLSX", DATA_DIR / "lookups.xlsx"))

TEMPLATE_DIR = BASE_DIR / "app" / "templates"
CERTIFICATE_TEMPLATE_PATH = TEMPLATE_DIR / "osvedcenie_z_template.docx"
INITIAL_RECORD_TEMPLATE_PATH = TEMPLATE_DIR / "prvotny_zaznam_z_template.docx"


def ensure_storage_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
