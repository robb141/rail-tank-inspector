import os
import re
import shutil
import subprocess
import threading
from pathlib import Path

from docxtpl import DocxTemplate

from app.config import (
    CERTIFICATE_TEMPLATE_PATH,
    GENERATED_DIR,
    INITIAL_RECORD_TEMPLATE_PATH,
    ensure_storage_dirs,
)
from app.models import Inspection


class PdfConversionUnavailable(RuntimeError):
    pass


PDF_CONVERSION_LOCK = threading.Lock()


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
            )
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
