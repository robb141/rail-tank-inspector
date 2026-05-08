from pathlib import Path

from docxtpl import DocxTemplate

from app.config import (
    CERTIFICATE_TEMPLATE_PATH,
    GENERATED_DIR,
    INITIAL_RECORD_TEMPLATE_PATH,
    ensure_storage_dirs,
)
from app.models import Inspection


def build_certificate_context(inspection: Inspection) -> dict[str, object]:
    return inspection.model_dump(mode="json")


def render_docx(template_path: Path, output_path: Path, inspection: Inspection) -> Path:
    ensure_storage_dirs()

    if not template_path.exists():
        raise FileNotFoundError(
            "Missing DOCX template. Put a docxtpl template at "
            f"{template_path}"
        )

    template = DocxTemplate(template_path)
    template.render(build_certificate_context(inspection))
    template.save(output_path)
    return output_path


def render_initial_record_docx(inspection: Inspection) -> Path:
    safe_number = inspection.certificate_number.replace("/", "-").replace(" ", "_")
    output_path = GENERATED_DIR / f"prvotny_zaznam_z_{inspection.id}_{safe_number}.docx"
    return render_docx(INITIAL_RECORD_TEMPLATE_PATH, output_path, inspection)


def render_certificate_docx(inspection: Inspection) -> Path:
    safe_number = inspection.certificate_number.replace("/", "-").replace(" ", "_")
    output_path = GENERATED_DIR / f"osvedcenie_z_{inspection.id}_{safe_number}.docx"
    return render_docx(CERTIFICATE_TEMPLATE_PATH, output_path, inspection)
