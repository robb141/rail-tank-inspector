from contextlib import asynccontextmanager
from pathlib import Path
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, GENERATED_DIR
from app.db.sqlite import (
    create_inspection,
    get_inspection,
    import_inspections,
    init_db,
    list_inspections,
    update_inspection,
)
from app.models import (
    Inspection,
    InspectionCreate,
    InspectionExport,
    InspectionImportRequest,
    InspectionImportResponse,
    InspectionResponse,
)
from app.services.documents import (
    PdfConversionUnavailable,
    find_libreoffice_converter,
    render_certificate_docx,
    render_certificate_pdf,
    render_initial_record_docx,
    render_initial_record_pdf,
)
from app.services.json_storage import save_inspection_json


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="Rail Tank Inspection MVP",
    version="0.1.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")


def document_url(path: Path | None) -> str | None:
    if path is None:
        return None
    return f"/documents/{path.name}"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/pdf")
def pdf_health() -> dict[str, str | bool | None]:
    converter = find_libreoffice_converter()
    return {
        "pdf_available": converter is not None,
        "libreoffice_path": converter,
    }


@app.get("/")
def root() -> FileResponse:
    return FileResponse(BASE_DIR / "app" / "static" / "index.html")


@app.post("/inspections", response_model=InspectionResponse)
def submit_inspection(payload: InspectionCreate) -> InspectionResponse:
    inspection = create_inspection(payload)
    json_path = save_inspection_json(inspection)
    initial_record_docx_path = render_initial_record_docx(inspection)

    certificate_docx_path = None
    if inspection.result == "pass":
        certificate_docx_path = render_certificate_docx(inspection)

    return InspectionResponse(
        inspection=inspection,
        json_path=str(json_path),
        initial_record_docx_path=str(initial_record_docx_path),
        initial_record_docx_url=document_url(initial_record_docx_path),
        certificate_docx_path=str(certificate_docx_path) if certificate_docx_path else None,
        certificate_docx_url=document_url(certificate_docx_path),
    )


@app.put("/inspections/{inspection_id}", response_model=InspectionResponse)
def replace_inspection(inspection_id: int, payload: InspectionCreate) -> InspectionResponse:
    inspection = update_inspection(inspection_id, payload)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")

    json_path = save_inspection_json(inspection)
    initial_record_docx_path = render_initial_record_docx(inspection)

    certificate_docx_path = None
    if inspection.result == "pass":
        certificate_docx_path = render_certificate_docx(inspection)

    return InspectionResponse(
        inspection=inspection,
        json_path=str(json_path),
        initial_record_docx_path=str(initial_record_docx_path),
        initial_record_docx_url=document_url(initial_record_docx_path),
        certificate_docx_path=str(certificate_docx_path) if certificate_docx_path else None,
        certificate_docx_url=document_url(certificate_docx_path),
    )


@app.get("/inspections", response_model=list[Inspection])
def read_inspections() -> list[Inspection]:
    return list_inspections()


@app.get("/admin/export", response_model=InspectionExport)
def export_inspections() -> InspectionExport:
    inspections = list_inspections()
    return InspectionExport(count=len(inspections), inspections=inspections)


@app.post("/admin/import", response_model=InspectionImportResponse)
def import_inspections_backup(payload: InspectionImportRequest) -> InspectionImportResponse:
    imported, skipped_duplicates = import_inspections(payload.inspections)
    return InspectionImportResponse(
        imported=imported,
        skipped_duplicates=skipped_duplicates,
    )


@app.get("/inspections/{inspection_id}", response_model=Inspection)
def read_inspection(inspection_id: int) -> Inspection:
    inspection = get_inspection(inspection_id)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@app.post("/inspections/{inspection_id}/certificate")
def generate_certificate(inspection_id: int) -> dict[str, str]:
    inspection = get_inspection(inspection_id)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if inspection.result != "pass":
        raise HTTPException(
            status_code=400,
            detail="Certificate can only be generated for a passing inspection",
        )

    output_path = render_certificate_docx(inspection)
    return {
        "certificate_docx_path": str(output_path),
        "certificate_docx_url": document_url(output_path),
    }


@app.post("/inspections/{inspection_id}/certificate/pdf")
def generate_certificate_pdf(inspection_id: int) -> dict[str, str]:
    inspection = get_inspection(inspection_id)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if inspection.result != "pass":
        raise HTTPException(
            status_code=400,
            detail="Certificate can only be generated for a passing inspection",
        )

    try:
        output_path = render_certificate_pdf(inspection)
    except PdfConversionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "certificate_pdf_path": str(output_path),
        "certificate_pdf_url": document_url(output_path),
    }


@app.post("/inspections/{inspection_id}/initial-record")
def generate_initial_record(inspection_id: int) -> dict[str, str]:
    inspection = get_inspection(inspection_id)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")

    output_path = render_initial_record_docx(inspection)
    return {
        "initial_record_docx_path": str(output_path),
        "initial_record_docx_url": document_url(output_path),
    }


@app.post("/inspections/{inspection_id}/initial-record/pdf")
def generate_initial_record_pdf(inspection_id: int) -> dict[str, str]:
    inspection = get_inspection(inspection_id)
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")

    try:
        output_path = render_initial_record_pdf(inspection)
    except PdfConversionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "initial_record_pdf_path": str(output_path),
        "initial_record_pdf_url": document_url(output_path),
    }


@app.get("/documents/{filename}")
def download_document(filename: str) -> FileResponse:
    path = (GENERATED_DIR / filename).resolve()
    generated_dir = GENERATED_DIR.resolve()
    if generated_dir not in path.parents or not path.exists() or path.suffix not in {".docx", ".pdf"}:
        raise HTTPException(status_code=404, detail="Document not found")

    media_type = "application/pdf"
    if path.suffix == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path,
        media_type=media_type,
        filename=path.name,
    )
