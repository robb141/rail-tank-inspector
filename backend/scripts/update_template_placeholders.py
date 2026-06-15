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
        paragraph_properties = ET.SubElement(paragraph, w("pPr"))
        spacing = ET.SubElement(paragraph_properties, w("spacing"))
        spacing.set(w("before"), "0")
        spacing.set(w("after"), "0")
        spacing.set(w("line"), "220")
        spacing.set(w("lineRule"), "auto")

        run = ET.SubElement(paragraph, w("r"))
        run_properties = ET.SubElement(run, w("rPr"))
        size = ET.SubElement(run_properties, w("sz"))
        size.set(w("val"), "18")
        size_complex = ET.SubElement(run_properties, w("szCs"))
        size_complex.set(w("val"), "18")

        text_node = ET.SubElement(run, w("t"))
        if line.startswith(" ") or line.endswith(" "):
            text_node.set(f"{{{XML_NS}}}space", "preserve")
        text_node.text = line

        if index < len(text.splitlines()) - 1:
            ET.SubElement(run, w("br"))


def ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(f"w:{tag}", NS)
    if child is None:
        child = ET.Element(w(tag))
        parent.insert(0, child)
    return child


def set_cell_width(cell: ET.Element, width: int, grid_span: int | None = None) -> None:
    tc_properties = ensure_child(cell, "tcPr")
    width_element = tc_properties.find("w:tcW", NS)
    if width_element is None:
        width_element = ET.SubElement(tc_properties, w("tcW"))
    width_element.set(w("w"), str(width))
    width_element.set(w("type"), "dxa")

    grid_span_element = tc_properties.find("w:gridSpan", NS)
    if grid_span is None or grid_span <= 1:
        if grid_span_element is not None:
            tc_properties.remove(grid_span_element)
        return

    if grid_span_element is None:
        grid_span_element = ET.SubElement(tc_properties, w("gridSpan"))
    grid_span_element.set(w("val"), str(grid_span))


def set_table_grid(table: ET.Element, widths: list[int]) -> None:
    table_grid = table.find("w:tblGrid", NS)
    if table_grid is None:
        table_grid = ET.Element(w("tblGrid"))
        table.insert(0, table_grid)

    for child in list(table_grid):
        table_grid.remove(child)

    for width in widths:
        grid_column = ET.SubElement(table_grid, w("gridCol"))
        grid_column.set(w("w"), str(width))


def remove_cells_after(row: ET.Element, keep_count: int) -> None:
    row_cells = cells(row)
    for cell in row_cells[keep_count:]:
        row.remove(cell)


def collapse_duplicated_table_columns(table: ET.Element) -> None:
    full_width = 10774
    half_width = full_width // 2
    set_table_grid(table, [half_width, full_width - half_width])

    for row in rows(table):
        row_cells = cells(row)
        if len(row_cells) >= 4:
            remove_cells_after(row, 2)
            set_cell_width(cells(row)[0], half_width)
            set_cell_width(cells(row)[1], full_width - half_width)
        elif len(row_cells) >= 2:
            remove_cells_after(row, 1)
            set_cell_width(cells(row)[0], full_width, grid_span=2)


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
    form_values = {
        1: "Označenie cisterny\n(č. vozňa): {{ tank_identification }}",
        3: "Miesto skúšky: {{ inspection_place }}    Dátum skúšky: {{ inspection_date }}",
        4: "č. zákazky / č. objednávky: {{ order_number }}",
        5: "Poradové číslo / číslo certifikátu: {{ certificate_number }}",
        7: "Číslo kotla: {{ tank_serial_number }}    Rok výroby: {{ year_of_manufacture }}",
        8: "Číslo schválenia typu: {{ type_approval_number }}",
        9: "Názov výrobcu kotla: {{ tank_manufacturer_name }}",
        10: "Objem v litroch: {{ capacity_liters }}    Držiteľ: {{ holder_name }}",
        11: "Dátum a druh poslednej skúšky: {{ last_inspection_date_type }}",
        14: "Tankcode: {{ tank_code }}    Aktuálna skúška: {{ current_inspection_type_label }}",
        15: "Ložný tovar: {{ cargo_substances }}",
        17: "Prac. tlak: {{ working_pressure }} bar",
        18: "Skúšobný tlak: {{ test_pressure }} bar",
        19: "Výpočtový tlak: {{ calculation_pressure }} bar",
        20: "Aktual. skúš. tlak: {{ current_test_pressure }} bar",
        22: "Vonk. prehliadka: {{ external_inspection_result_label }}    Vnút. prehliadka: {{ internal_inspection_result_label }}",
        23: "Kontr. zvarov: {{ weld_inspection_result_label }}    Kontr. štítkov: {{ plate_inspection_result_label }}",
        24: "Preh. vykur. hadov: vonk. {{ heating_coils_external_result_label }}    vnút. {{ heating_coils_internal_result_label }}",
        25: "Bočné (výpus.) ventily: I.str. {{ side_valves_side_1_result_label }}    II.str. {{ side_valves_side_2_result_label }}",
        26: "Stredový ventil: {{ center_valve_result_label }}",
        27: "veko + tesnenie: {{ lid_gasket_result_label }}",
        28: "Typ poist. ventilu: {{ safety_valve_type }}    č. PV: {{ safety_valve_number }}",
        29: "pretlak: {{ safety_valve_pressure }}    podtlak: {{ vacuum_valve_pressure }}",
        31: "Uzemnenie: {{ grounding_result_label }}",
        32: "Protokol UTT: {{ utt_protocol_number }}    Protokol gum.: {{ rubber_protocol_number }}",
        33: "Nameraná min. hrúbka kotla:",
        36: "Orazenie štítka: {{ tank_plate_stamp }}",
        37: "Budúca skúška: {{ next_inspection }}",
        38: "Zvláštne ustanovenia: {{ special_provisions }}",
        39: "č. mer. + kal. do: {{ measuring_device_number }} / {{ calibration_valid_until }}",
        40: "Čas trvania skúšky: {{ test_duration }}",
        41: "Poznámky:\n{{ remarks }}\nDôvod mimoriadnej kontroly: {{ extraordinary_inspection_reason }}",
    }

    for table in tables(root):
        collapse_duplicated_table_columns(table)

    for row_number, value in form_values.items():
        row_cells = cells(rows(main_table)[row_number - 1])
        set_cell_text(row_cells[0], value)

    row_12_cells = cells(rows(main_table)[11])
    set_cell_text(row_12_cells[0], "P: {{ periodic_inspection_date }}")
    set_cell_text(row_12_cells[1], "L: {{ intermediate_inspection_date }}")

    row_34_cells = cells(rows(main_table)[33])
    set_cell_text(row_34_cells[0], "čelá: {{ measured_wall_thickness_front_mm }} mm")
    set_cell_text(row_34_cells[1], "luby: {{ measured_wall_thickness_shell_mm }} mm")

    for table in tables(root)[1:]:
        for row in rows(table):
            row_cells = cells(row)
            if not row_cells:
                continue
            text = cell_text(row_cells[0])
            if "Vlastníka zariadenia" in text:
                value = "Vlastníka zariadenia: {{ supplier_device_owner }}"
            elif "Druh zariadenia" in text:
                value = "Druh zariadenia: {{ supplier_device_type }}"
            elif "Výrobné číslo zariadenia" in text:
                value = "Výrobné číslo zariadenia: {{ supplier_device_serial_number }}"
            elif "Platnosť kalibrácie" in text:
                value = "Platnosť kalibrácie: {{ supplier_calibration_validity }}"
            elif "Názov spoločnosti" in text:
                value = "Názov spoločnosti, ktorá vykonala kalibráciu: {{ supplier_calibration_company }}"
            elif "Registračné číslo SNAS" in text:
                value = "Registračné číslo SNAS: {{ supplier_snas_registration_number }}"
            elif "Iné zistenia" in text:
                value = "Iné zistenia:\n{{ supplier_other_findings }}"
            else:
                continue

            set_cell_text(row_cells[0], value)


def main() -> None:
    replace_document_xml(TEMPLATES / "osvedcenie_z_template.docx", update_certificate)
    replace_document_xml(TEMPLATES / "prvotny_zaznam_z_template.docx", update_initial_record)


if __name__ == "__main__":
    main()
