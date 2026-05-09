from app.models import Inspection


def test_document_paths_use_readable_safe_filenames(isolated_modules, sample_payload):
    documents = isolated_modules["app.services.documents"]

    inspection = Inspection.model_validate({
        **sample_payload,
        "id": 42,
        "created_at": "2026-05-09T12:00:00+00:00",
    })

    initial_path = documents.render_initial_record_docx(inspection)
    certificate_path = documents.render_certificate_docx(inspection)

    assert initial_path.name == (
        "Z-2026-0001_33-56-7920-123-4_prvotny-zaznam-z_id-42.docx"
    )
    assert certificate_path.name == (
        "Z-2026-0001_33-56-7920-123-4_osvedcenie-z_id-42.docx"
    )
    assert initial_path.exists()
    assert certificate_path.exists()


def test_safe_filename_part_has_fallback(isolated_modules):
    documents = isolated_modules["app.services.documents"]

    assert documents.safe_filename_part(" / ") == "bez-cisla"
    assert documents.safe_filename_part("A/B 123") == "A-B-123"
