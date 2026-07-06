from zipfile import ZipFile
from xml.etree import ElementTree as ET

from app.models import Inspection


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WORD_NAMESPACES = {"w": WORD_NS}


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


def test_certificate_context_computes_labels_and_thickness(isolated_modules, sample_payload):
    from test_lookups import build_lookups_file

    config = isolated_modules["app.config"]
    documents = isolated_modules["app.services.documents"]
    build_lookups_file(config.LOOKUPS_XLSX_PATH)

    inspection = Inspection.model_validate({
        **sample_payload,
        "id": 7,
        "created_at": "2026-05-09T12:00:00+00:00",
        "type_approval_number": "CZ-DU-C 133.01",
        "tank_code": "L4BH",
        "periodic_inspection_date": "2022-07-06",
        "measured_wall_thickness_front_mm": "6,5",
        "measured_wall_thickness_shell_mm": "6,4",
    })

    context = documents.build_certificate_context(inspection)

    assert context["periodic_inspection_date"] == "6.7.2022"
    assert context["last_inspection_label"] == "Periodická kontrola (P) 6.7.2022"
    assert context["shell_thickness_required_measured"] == "5,8 mm / 6,5 mm*"
    assert context["head_thickness_required_measured"] == "6,1 mm / 6,4 mm*"


def test_certificate_context_without_lookup_match(isolated_modules, sample_payload):
    documents = isolated_modules["app.services.documents"]

    inspection = Inspection.model_validate({
        **sample_payload,
        "id": 8,
        "created_at": "2026-05-09T12:00:00+00:00",
        "type_approval_number": "NEZNAME-123",
        "intermediate_inspection_date": "2024-01-31",
    })

    context = documents.build_certificate_context(inspection)

    assert context["last_inspection_label"] == "Medzikontrola (L) 31.1.2024"
    assert context["shell_thickness_required_measured"] == "- / *"
    assert context["head_thickness_required_measured"] == "- / *"


def test_safe_filename_part_has_fallback(isolated_modules):
    documents = isolated_modules["app.services.documents"]

    assert documents.safe_filename_part(" / ") == "bez-cisla"
    assert documents.safe_filename_part("A/B 123") == "A-B-123"


def test_initial_record_template_has_no_duplicated_row_columns(isolated_modules):
    config = isolated_modules["app.config"]

    with ZipFile(config.INITIAL_RECORD_TEMPLATE_PATH) as docx_file:
        document_xml = docx_file.read("word/document.xml")

    root = ET.fromstring(document_xml)
    for table in root.findall(".//w:tbl", WORD_NAMESPACES):
        for row in table.findall("./w:tr", WORD_NAMESPACES):
            cell_texts = [
                "".join(
                    text_node.text or ""
                    for text_node in cell.findall(".//w:t", WORD_NAMESPACES)
                ).strip()
                for cell in row.findall("./w:tc", WORD_NAMESPACES)
            ]
            non_empty_texts = [text for text in cell_texts if text]

            assert len(non_empty_texts) == len(set(non_empty_texts))
