import os
import re
import shutil
import subprocess
import threading
from datetime import date
from pathlib import Path

from docxtpl import DocxTemplate

from app.config import (
    CERTIFICATE_TEMPLATE_PATH,
    GENERATED_DIR,
    INITIAL_RECORD_TEMPLATE_PATH,
    ensure_storage_dirs,
)
from app.models import Inspection, LookupTankType
from app.services import lookups


class PdfConversionUnavailable(RuntimeError):
    pass


PDF_CONVERSION_LOCK = threading.Lock()
PDF_CONVERSION_TIMEOUT_SECONDS = 120


def find_libreoffice_converter() -> str | None:
    configured_path = os.getenv("LIBREOFFICE_PATH")
    if configured_path and Path(configured_path).exists():
        return configured_path

    for executable in ("soffice", "libreoffice"):
        converter = shutil.which(executable)
        if converter:
            return converter

    common_paths = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/libreoffice",
        "/usr/local/bin/libreoffice",
        "/opt/libreoffice/program/soffice",
        "C:/Program Files/LibreOffice/program/soffice.exe",
        "C:/Program Files (x86)/LibreOffice/program/soffice.exe",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path

    return None


RESULT_LABELS = {
    "pass": "V",
    "fail": "N",
    "not_applicable": "-",
}

INSPECTION_TYPE_LABELS = {
    "initial": "Východisková",
    "periodic": "Periodická P",
    "intermediate": "Medzikontrola L",
    "exceptional": "Mimoriadna",
}


def format_slovak_date(value: object) -> object:
    if not value:
        return value
    try:
        parsed = date.fromisoformat(str(value))
    except ValueError:
        return value
    return parsed.strftime("%d.%m.%Y")


def find_tank_type(inspection: Inspection) -> LookupTankType | None:
    if not inspection.type_approval_number:
        return None
    try:
        tank_types = lookups.load_lookups().tank_types
    except Exception:
        return None
    candidates = [
        tank_type
        for tank_type in tank_types
        if tank_type.type_approval_number == inspection.type_approval_number
    ]
    if not candidates:
        return None
    if inspection.tank_code:
        for candidate in candidates:
            if candidate.tank_code == inspection.tank_code:
                return candidate
    return candidates[0]


def format_thickness(required: object, measured: object) -> str:
    required_text = str(required).replace(".", ",") if required else ""
    measured_text = str(measured).replace(".", ",") if measured else ""
    required_part = f"{required_text} mm" if required_text else "-"
    measured_part = f"{measured_text} mm*" if measured_text else "*"
    return f"{required_part} / {measured_part}"


def without_bar(value: object) -> object:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    lowered = stripped.lower()
    if lowered.endswith(" bar"):
        return stripped[:-4].strip()
    return stripped


def build_certificate_context(inspection: Inspection) -> dict[str, object]:
    context = {
        key: "" if value is None else value
        for key, value in inspection.model_dump(mode="json").items()
    }
    result_fields = [
        "result",
        "external_inspection_result",
        "internal_inspection_result",
        "weld_inspection_result",
        "plate_inspection_result",
        "heating_coils_external_result",
        "heating_coils_internal_result",
        "side_valves_side_1_result",
        "side_valves_side_2_result",
        "center_valve_result",
        "lid_gasket_result",
        "grounding_result",
    ]
    for field in result_fields:
        value = context.get(field)
        context[f"{field}_label"] = RESULT_LABELS.get(value, value or "")

    inspection_type = context.get("current_inspection_type")
    context["current_inspection_type_label"] = INSPECTION_TYPE_LABELS.get(
        inspection_type,
        inspection_type or "",
    )
    for type_key in INSPECTION_TYPE_LABELS:
        context[f"inspection_type_{type_key}_mark"] = (
            "X" if inspection_type == type_key else ""
        )

    pressure_fields = [
        "test_pressure",
        "working_pressure",
        "calculation_pressure",
        "current_test_pressure",
        "safety_valve_pressure",
        "vacuum_valve_pressure",
    ]
    for field in pressure_fields:
        context[field] = without_bar(context.get(field))

    for field in ("inspection_date", "periodic_inspection_date", "intermediate_inspection_date"):
        context[field] = format_slovak_date(context.get(field))

    label_parts = []
    if context["periodic_inspection_date"]:
        label_parts.append(f"Periodická kontrola (P) {context['periodic_inspection_date']}")
    if context["intermediate_inspection_date"]:
        label_parts.append(f"Medzikontrola (L) {context['intermediate_inspection_date']}")
    context["last_inspection_label"] = ", ".join(label_parts)

    tank_type = find_tank_type(inspection)
    context["shell_thickness_required_measured"] = format_thickness(
        tank_type.shell_thickness if tank_type else None,
        inspection.measured_wall_thickness_front_mm,
    )
    context["head_thickness_required_measured"] = format_thickness(
        tank_type.head_thickness if tank_type else None,
        inspection.measured_wall_thickness_shell_mm,
    )

    return context


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


def safe_filename_part(value: object, fallback: str = "bez-cisla") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip())
    cleaned = cleaned.strip("-._")
    return cleaned or fallback


def document_stem(inspection: Inspection, document_type: str) -> str:
    certificate_number = safe_filename_part(inspection.certificate_number)
    tank_identification = safe_filename_part(inspection.tank_identification, "bez-cisterny")
    return f"{certificate_number}_{tank_identification}_{document_type}_id-{inspection.id}"


def delete_generated_documents(inspection_id: int) -> None:
    ensure_storage_dirs()
    for path in GENERATED_DIR.glob(f"*_id-{inspection_id}.*"):
        path.unlink(missing_ok=True)


def render_initial_record_docx(inspection: Inspection) -> Path:
    output_path = GENERATED_DIR / f"{document_stem(inspection, 'prvotny-zaznam-z')}.docx"
    return render_docx(INITIAL_RECORD_TEMPLATE_PATH, output_path, inspection)


def render_certificate_docx(inspection: Inspection) -> Path:
    output_path = GENERATED_DIR / f"{document_stem(inspection, 'osvedcenie-z')}.docx"
    return render_docx(CERTIFICATE_TEMPLATE_PATH, output_path, inspection)


def convert_docx_to_pdf(docx_path: Path) -> Path:
    ensure_storage_dirs()

    converter = find_libreoffice_converter()
    if converter is None:
        raise PdfConversionUnavailable(
            "LibreOffice was not found on the backend machine. Install LibreOffice "
            "or set LIBREOFFICE_PATH to the soffice executable."
        )

    with PDF_CONVERSION_LOCK:
        try:
            result = subprocess.run(
                [
                    converter,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(GENERATED_DIR),
                    str(docx_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=PDF_CONVERSION_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "LibreOffice PDF conversion timed out after "
                f"{PDF_CONVERSION_TIMEOUT_SECONDS} seconds."
            ) from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or str(exc)).strip()
            raise RuntimeError(f"LibreOffice PDF conversion failed: {details}") from exc

        pdf_path = GENERATED_DIR / f"{docx_path.stem}.pdf"
        if not pdf_path.exists():
            details = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"PDF conversion failed. Expected output was {pdf_path}. {details}"
            )

        return pdf_path


def render_initial_record_pdf(inspection: Inspection) -> Path:
    return convert_docx_to_pdf(render_initial_record_docx(inspection))


def render_certificate_pdf(inspection: Inspection) -> Path:
    return convert_docx_to_pdf(render_certificate_docx(inspection))
