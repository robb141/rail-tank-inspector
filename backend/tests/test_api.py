def test_submit_update_and_read_inspection(test_client, sample_payload):
    create_response = test_client.post("/inspections", json=sample_payload)
    assert create_response.status_code == 200
    created_body = create_response.json()
    inspection_id = created_body["inspection"]["id"]

    assert created_body["inspection"]["certificate_number"] == "Z/2026 0001"
    assert created_body["initial_record_docx_url"].endswith(
        "Z-2026-0001_33-56-7920-123-4_prvotny-zaznam-z_id-1.docx"
    )
    assert created_body["certificate_docx_url"].endswith(
        "Z-2026-0001_33-56-7920-123-4_osvedcenie-z_id-1.docx"
    )

    update_response = test_client.put(
        f"/inspections/{inspection_id}",
        json={**sample_payload, "holder_name": "Updated Holder", "result": "fail"},
    )
    assert update_response.status_code == 200
    updated_body = update_response.json()

    assert updated_body["inspection"]["id"] == inspection_id
    assert updated_body["inspection"]["holder_name"] == "Updated Holder"
    assert updated_body["inspection"]["result"] == "fail"
    assert updated_body["certificate_docx_url"] is None

    read_response = test_client.get(f"/inspections/{inspection_id}")
    assert read_response.status_code == 200
    assert read_response.json()["holder_name"] == "Updated Holder"


def test_failing_inspection_cannot_generate_certificate(test_client, sample_payload):
    create_response = test_client.post(
        "/inspections",
        json={**sample_payload, "certificate_number": "Z-FAIL-001", "result": "fail"},
    )
    assert create_response.status_code == 200
    inspection_id = create_response.json()["inspection"]["id"]

    certificate_response = test_client.post(f"/inspections/{inspection_id}/certificate")

    assert certificate_response.status_code == 400
    assert certificate_response.json()["detail"] == (
        "Certificate can only be generated for a passing inspection"
    )


def test_admin_export_and_import_skip_duplicates(test_client, sample_payload):
    create_response = test_client.post("/inspections", json=sample_payload)
    assert create_response.status_code == 200

    export_response = test_client.get("/admin/export")
    assert export_response.status_code == 200
    export_body = export_response.json()
    assert export_body["count"] == 1

    import_response = test_client.post("/admin/import", json=export_body)
    assert import_response.status_code == 200
    assert import_response.json() == {
        "imported": 0,
        "skipped_duplicates": 1,
    }
