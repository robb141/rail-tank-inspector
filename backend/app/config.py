from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json"
GENERATED_DIR = DATA_DIR / "generated"
DB_PATH = DATA_DIR / "rail_inspections.sqlite3"

TEMPLATE_DIR = BASE_DIR / "app" / "templates"
CERTIFICATE_TEMPLATE_PATH = TEMPLATE_DIR / "osvedcenie_z_template.docx"
INITIAL_RECORD_TEMPLATE_PATH = TEMPLATE_DIR / "prvotny_zaznam_z_template.docx"


def ensure_storage_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
