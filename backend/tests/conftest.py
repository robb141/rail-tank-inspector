import importlib
import sys

import pytest


APP_MODULES = [
    "app.config",
    "app.db.sqlite",
    "app.services.json_storage",
    "app.services.documents",
    "app.main",
]


@pytest.fixture()
def isolated_modules(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("RAIL_INSPECT_DATA_DIR", str(data_dir))

    loaded_modules = {}
    for module_name in APP_MODULES:
        if module_name in sys.modules:
            loaded_modules[module_name] = importlib.reload(sys.modules[module_name])
        else:
            loaded_modules[module_name] = importlib.import_module(module_name)

    return loaded_modules


@pytest.fixture()
def sample_payload():
    return {
        "certificate_number": "Z/2026 0001",
        "holder_name": "Rail Tank Services s.r.o.",
        "holder_street": "Mikoviniho 19",
        "holder_postal_code": "917 02",
        "holder_city": "Trnava",
        "holder_country": "Slovenska republika",
        "type_approval_number": "E1-ADR-12345",
        "tank_manufacturer_name": "Tatra Vagonka",
        "tank_serial_number": "KOT-98765",
        "year_of_manufacture": 2018,
        "tank_identification": "33 56 7920 123-4",
        "tank_code": "L4BH",
        "test_pressure": "4 bar",
        "working_pressure": "3 bar",
        "inspection_place": "Bratislava",
        "inspection_date": "2026-05-09",
        "next_inspection": "05/2029",
        "inspector_name": "Ing. Jan Kontrolor",
        "result": "pass",
        "remarks": "Bez zistenych nedostatkov.",
    }


@pytest.fixture()
def test_client(isolated_modules):
    from fastapi.testclient import TestClient

    app = isolated_modules["app.main"].app
    with TestClient(app) as client:
        yield client
