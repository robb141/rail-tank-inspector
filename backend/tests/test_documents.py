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
