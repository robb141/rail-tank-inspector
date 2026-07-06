from openpyxl import Workbook


def build_lookups_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()

    holders = workbook.active
    holders.title = "Ziadatel-Drzitel"
    holders.append([])
    holders.append([None, "Žiadateľ / Držiteľ", "Ulica", "PSČ", "Mesto ", "Štát"])
    holders.append([None, "Firma A s.r.o.", "Hlavná 1", "917 02", "Trnava", "SR"])
    holders.append([None, None, None, None, None, None])
    holders.append([None, "Firma B", "Dombóvári út 28", 1117, "Budapest", "HU"])

    tank_types = workbook.create_sheet("Typ cisterny")
    tank_types.append([])
    tank_types.append([
        None,
        "Číslo schválenia typu",
        "Názov výrobcu",
        "Kód cisterny",
        "Hrúbka steny cisterny",
        "Hrúbka steny dien",
        "Skúšobný tlak",
        "Najvyšší dovolený pracovný tlak",
        "Výpočtový pretlak - vnútorný ",
        "Výpočtový podtlak",
    ])
    tank_types.append(
        [None, "CZ-DU-C 133.01", "NYMWAG CS a.s.", "L4BH", 5.8, "6,1", 4, 3, 4.5, 0.4]
    )

    workbook.save(path)


def test_lookups_endpoint_parses_workbook(test_client, isolated_modules):
    config = isolated_modules["app.config"]
    build_lookups_file(config.LOOKUPS_XLSX_PATH)

    response = test_client.get("/lookups")
    assert response.status_code == 200
    body = response.json()

    assert [holder["holder_name"] for holder in body["holders"]] == [
        "Firma A s.r.o.",
        "Firma B",
    ]
    assert body["holders"][0]["holder_street"] == "Hlavná 1"
    assert body["holders"][1]["holder_postal_code"] == "1117"

    assert body["tank_types"] == [
        {
            "type_approval_number": "CZ-DU-C 133.01",
            "tank_manufacturer_name": "NYMWAG CS a.s.",
            "tank_code": "L4BH",
            "shell_thickness": "5.8",
            "head_thickness": "6,1",
            "test_pressure": "4",
            "working_pressure": "3",
            "calculation_pressure": "4.5",
            "calculation_vacuum": "0.4",
        },
    ]


def test_lookups_endpoint_with_missing_file(test_client):
    response = test_client.get("/lookups")
    assert response.status_code == 200
    assert response.json() == {"holders": [], "tank_types": []}
