from app.models import InspectionCreate, InspectionImportItem


def test_create_update_and_list_inspections(isolated_modules, sample_payload):
    sqlite = isolated_modules["app.db.sqlite"]
    sqlite.init_db()

    created = sqlite.create_inspection(InspectionCreate.model_validate(sample_payload))
    updated_payload = InspectionCreate.model_validate({
        **sample_payload,
        "holder_name": "Updated Holder",
        "result": "fail",
    })
    updated = sqlite.update_inspection(created.id, updated_payload)

    assert updated is not None
    assert updated.id == created.id
    assert updated.created_at == created.created_at
    assert updated.holder_name == "Updated Holder"
    assert updated.result == "fail"

    inspections = sqlite.list_inspections()
    assert len(inspections) == 1
    assert inspections[0].id == created.id
    assert inspections[0].holder_name == "Updated Holder"


def test_import_skips_duplicate_inspections(isolated_modules, sample_payload):
    sqlite = isolated_modules["app.db.sqlite"]
    sqlite.init_db()

    item = InspectionImportItem.model_validate({
        **sample_payload,
        "created_at": "2026-05-09T12:00:00+00:00",
    })

    imported, skipped = sqlite.import_inspections([item, item])

    assert imported == 1
    assert skipped == 1
    assert len(sqlite.list_inspections()) == 1
