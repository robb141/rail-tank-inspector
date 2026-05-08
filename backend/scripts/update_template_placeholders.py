from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "templates"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}

ET.register_namespace("w", W_NS)


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def replace_document_xml(docx_path: Path, transform) -> None:
    with ZipFile(docx_path, "r") as source:
        document_xml = source.read("word/document.xml")
        root = ET.fromstring(document_xml)
        transform(root)

        updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_path = Path(tmp_file.name)

        with ZipFile(tmp_path, "w", ZIP_DEFLATED) as target:
            for item in source.infolist():
                if item.filename == "word/document.xml":
                    target.writestr(item, updated_xml)
                else:
                    target.writestr(item, source.read(item.filename))

    shutil.move(tmp_path, docx_path)


def cell_text(cell: ET.Element) -> str:
    return "".join(text.text or "" for text in cell.findall(".//w:t", NS)).strip()


def set_cell_text(cell: ET.Element, text: str) -> None:
    tc_properties = cell.find("w:tcPr", NS)
    for child in list(cell):
        if child is not tc_properties:
            cell.remove(child)

    for index, line in enumerate(text.splitlines()):
        paragraph = ET.SubElement(cell, w("p"))
        run = ET.SubElement(paragraph, w("r"))
        text_node = ET.SubElement(run, w("t"))
        if line.startswith(" ") or line.endswith(" "):
            text_node.set(f"{{{XML_NS}}}space", "preserve")
        text_node.text = line

        if index < len(text.splitlines()) - 1:
            ET.SubElement(run, w("br"))


def tables(root: ET.Element) -> list[ET.Element]:
    return root.findall(".//w:tbl", NS)


def rows(table: ET.Element) -> list[ET.Element]:
    return table.findall("./w:tr", NS)


def cells(row: ET.Element) -> list[ET.Element]:
    return row.findall("./w:tc", NS)


def set_cell(table: ET.Element, row_number: int, cell_number: int, text: str) -> None:
    set_cell_text(cells(rows(table)[row_number - 1])[cell_number - 1], text)


def update_certificate(root: ET.Element) -> None:
    table_1, table_2 = tables(root)[:2]

    first_table_values = {
        (3, 2): "{{ certificate_number }}",
        (4, 2): "{{ holder_name }}",
        (5, 2): "{{ holder_street }}",
        (6, 2): "{{ holder_postal_code }}",
        (7, 2): "{{ holder_city }}",
        (8, 2): "{{ holder_country }}",
        (10, 2): "{{ type_approval_number }}",
        (11, 2): "{{ tank_manufacturer_name }}",
        (12, 2): "{{ tank_serial_number }}",
        (13, 2): "{{ year_of_manufacture }}",
        (15, 2): "{{ tank_identification }}",
        (16, 1): "Zvláštne ustanovenia (Special provisions): {{ special_provisions }}",
        (16, 2): "Kód cisterny (Tank code): {{ tank_code }}",
        (20, 2): "{{ test_pressure }} bar",
        (21, 2): "{{ working_pressure }} bar",
        (22, 2): "{{ calculation_pressure }} bar",
        (24, 2): "{{ safety_valve_pressure }} bar**",
        (25, 2): "{{ vacuum_valve_pressure }} bar**",
        (27, 7): "{{ capacity_liters }}",
    }
    for coordinates, value in first_table_values.items():
        set_cell(table_1, *coordinates, value)

    set_cell(
        table_2,
        15,
        1,
        "Poznámky:\n"
        "{{ remarks }}\n"
        "Ložné látky: {{ cargo_substances }}\n"
        "* Hrúbka skutočne nameraná je uvedená v priloženom protokole.\n"
        "** Nastavenie poistných ventilov podľa priloženého protokolu.",
    )
    set_cell(table_2, 18, 2, "{{ tank_plate_stamp }}")
    set_cell(table_2, 19, 2, "{{ next_inspection }}")
    set_cell(table_2, 20, 1, "Miesto a dátum kontroly\n{{ inspection_place }}, {{ inspection_date }}")
    set_cell(table_2, 20, 2, "Dátum vydania\n{{ inspection_date }}")
    set_cell(table_2, 20, 3, "Meno inšpektora, podpis a pečiatka\n{{ inspector_name }}")


def update_initial_record(root: ET.Element) -> None:
    main_table = tables(root)[0]
    duplicated_form_values = {
        1: "Označenie cisterny\n(č. vozňa): {{ tank_identification }}",
        3: "Miesto skúšky: {{ inspection_place }}    Dátum skúšky: {{ inspection_date }}",
        5: "Poradové číslo / číslo certifikátu: {{ certificate_number }}",
        7: "Číslo kotla: {{ tank_serial_number }}    Rok výroby: {{ year_of_manufacture }}",
        8: "Číslo schválenia typu: {{ type_approval_number }}",
        9: "Názov výrobcu kotla: {{ tank_manufacturer_name }}",
        10: "Objem v litroch: {{ capacity_liters }}    Držiteľ: {{ holder_name }}",
        14: "Tankcode: {{ tank_code }}    Aktuálna skúška: {{ result }}",
        15: "Ložný tovar: {{ cargo_substances }}",
        17: "Prac. tlak: {{ working_pressure }} bar",
        18: "Skúšobný tlak: {{ test_pressure }} bar",
        19: "Výpočtový tlak: {{ calculation_pressure }} bar",
        29: "pretlak: {{ safety_valve_pressure }}    podtlak: {{ vacuum_valve_pressure }}",
        36: "Orazenie štítka: {{ tank_plate_stamp }}",
        37: "Budúca skúška: {{ next_inspection }}",
        38: "Zvláštne ustanovenia: {{ special_provisions }}",
        41: "Poznámky:\n{{ remarks }}\nDôvod mimoriadnej kontroly:",
    }

    for row_number, value in duplicated_form_values.items():
        row_cells = cells(rows(main_table)[row_number - 1])
        set_cell_text(row_cells[0], value)
        set_cell_text(row_cells[-1], value)


def main() -> None:
    replace_document_xml(TEMPLATES / "osvedcenie_z_template.docx", update_certificate)
    replace_document_xml(TEMPLATES / "prvotny_zaznam_z_template.docx", update_initial_record)


if __name__ == "__main__":
    main()
