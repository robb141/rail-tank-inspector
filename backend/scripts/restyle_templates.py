"""Restyle the DOCX templates.

- prvotny_zaznam_z: drop the stray line break after "Označenie cisterny",
  render all placeholder values in bold, and use the computed
  last_inspection_label instead of the removed form field.
- osvedcenie_z: center value paragraphs, fill "Dátum a druh poslednej
  kontroly" with the computed label, and replace the fixed wall-thickness
  values with required/measured placeholders.

Run from backend/: python scripts/restyle_templates.py
"""

import copy
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "app" / "templates"
PRVOTNY_PATH = TEMPLATE_DIR / "prvotny_zaznam_z_template.docx"
OSVEDCENIE_PATH = TEMPLATE_DIR / "osvedcenie_z_template.docx"

PLACEHOLDER_RE = re.compile(r"(\{\{[^{}]*\}\})")


def iter_cell_paragraphs(document):
    # Merged cells can be yielded more than once; every transformation
    # below is idempotent, so no deduplication is needed.
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs


def first_run_properties(paragraph):
    for run in paragraph.runs:
        if run._element.rPr is not None:
            return copy.deepcopy(run._element.rPr)
    return None


def rebuild_with_bold_placeholders(paragraph):
    text = paragraph.text
    if "{{" not in text:
        return
    properties = first_run_properties(paragraph)
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)
    for part in PLACEHOLDER_RE.split(text):
        if not part:
            continue
        run = paragraph.add_run(part)
        if properties is not None:
            run._element.insert(0, copy.deepcopy(properties))
        if part.startswith("{{"):
            run.bold = True


def replace_paragraph_text(paragraph, text, properties=None):
    if properties is None:
        properties = first_run_properties(paragraph)
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)
    run = paragraph.add_run(text)
    if properties is not None:
        run._element.insert(0, copy.deepcopy(properties))


def restyle_prvotny():
    document = Document(PRVOTNY_PATH)

    # 1. Remove the stray line break after "Označenie cisterny".
    fixed_breaks = 0
    for paragraph in iter_cell_paragraphs(document):
        if paragraph.text == "Označenie cisterny\n":
            for run in paragraph.runs:
                if run.text.endswith("\n"):
                    run.text = run.text.rstrip("\n")
                    fixed_breaks += 1

    # 2. Use the computed label for the last inspection line.
    swapped = 0
    for paragraph in iter_cell_paragraphs(document):
        if "{{ last_inspection_date_type }}" in paragraph.text:
            for run in paragraph.runs:
                if "{{ last_inspection_date_type }}" in run.text:
                    run.text = run.text.replace(
                        "{{ last_inspection_date_type }}",
                        "{{ last_inspection_label }}",
                    )
                    swapped += 1

    # 3. Bold every placeholder.
    bolded = 0
    for paragraph in iter_cell_paragraphs(document):
        if "{{" in paragraph.text:
            rebuild_with_bold_placeholders(paragraph)
            bolded += 1

    document.save(PRVOTNY_PATH)
    print(f"prvotny: breaks fixed={fixed_breaks}, label swapped={swapped}, "
          f"paragraphs bolded={bolded}")


def restyle_osvedcenie():
    document = Document(OSVEDCENIE_PATH)
    identification_table = document.tables[0]

    # Formatting reference: an existing value cell.
    reference_properties = first_run_properties(
        identification_table.rows[12].cells[-1].paragraphs[0]
    )

    filled_label = 0
    thickness = 0
    for row in identification_table.rows:
        # Materialize first so lxml proxies stay alive and ids are stable.
        row_cells = list(row.cells)
        cells, seen = [], set()
        for cell in row_cells:
            if id(cell._tc) not in seen:
                seen.add(id(cell._tc))
                cells.append(cell)
        if len(cells) < 2:
            continue
        label = cells[0].text
        value_cell = cells[-1]
        if label.startswith("Dátum a druh poslednej kontroly"):
            replace_paragraph_text(
                value_cell.paragraphs[0],
                "{{ last_inspection_label }}",
                reference_properties,
            )
            filled_label += 1
        elif label.startswith("Hrúbka steny cisterny"):
            replace_paragraph_text(
                value_cell.paragraphs[0], "{{ shell_thickness_required_measured }}"
            )
            thickness += 1
        elif label.startswith("Hrúbka steny dien"):
            replace_paragraph_text(
                value_cell.paragraphs[0], "{{ head_thickness_required_measured }}"
            )
            thickness += 1

    # Center every value paragraph (paragraphs that begin with a placeholder).
    centered = 0
    for paragraph in iter_cell_paragraphs(document):
        if paragraph.text.strip().startswith("{{"):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            centered += 1

    document.save(OSVEDCENIE_PATH)
    print(f"osvedcenie: label cells filled={filled_label}, "
          f"thickness cells={thickness}, paragraphs centered={centered}")


if __name__ == "__main__":
    restyle_prvotny()
    restyle_osvedcenie()
