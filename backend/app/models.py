from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InspectionCreate(BaseModel):
    certificate_number: str = Field(..., examples=["Z-2026-0001"])
    holder_name: str = Field(..., examples=["Rail Tank Services s.r.o."])
    holder_street: Optional[str] = Field(None, examples=["Mikovíniho 19"])
    holder_postal_code: Optional[str] = Field(None, examples=["917 02"])
    holder_city: Optional[str] = Field(None, examples=["Trnava"])
    holder_country: Optional[str] = Field(None, examples=["Slovenská republika"])
    type_approval_number: Optional[str] = Field(None, examples=["E1-ADR-12345"])
    tank_manufacturer_name: Optional[str] = Field(None, examples=["Tatra Vagónka"])
    tank_serial_number: Optional[str] = Field(None, examples=["KOT-98765"])
    year_of_manufacture: Optional[int] = Field(None, ge=1000, le=2100, examples=[2018])
    tank_identification: str = Field(..., examples=["33 56 7920 123-4"])
    tank_code: Optional[str] = Field(None, examples=["L4BH"])
    order_number: Optional[str] = Field(None, examples=["OBJ-2026-15"])
    last_inspection_date_type: Optional[str] = Field(None, examples=["05/2023 P"])
    periodic_inspection_date: Optional[str] = Field(None, examples=["05/2023"])
    intermediate_inspection_date: Optional[str] = Field(None, examples=["05/2024"])
    current_inspection_type: Optional[str] = Field(None, examples=["periodic"])
    test_pressure: Optional[str] = Field(None, examples=["4 bar"])
    working_pressure: Optional[str] = Field(None, examples=["3 bar"])
    calculation_pressure: Optional[str] = Field(None, examples=["4.5 bar"])
    current_test_pressure: Optional[str] = Field(None, examples=["4 bar"])
    safety_valve_pressure: Optional[str] = Field(None, examples=["3.3 bar"])
    vacuum_valve_pressure: Optional[str] = Field(None, examples=["-0.21 bar"])
    external_inspection_result: Optional[str] = Field(None, examples=["pass"])
    internal_inspection_result: Optional[str] = Field(None, examples=["pass"])
    weld_inspection_result: Optional[str] = Field(None, examples=["pass"])
    plate_inspection_result: Optional[str] = Field(None, examples=["pass"])
    heating_coils_external_result: Optional[str] = Field(None, examples=["not_applicable"])
    heating_coils_internal_result: Optional[str] = Field(None, examples=["not_applicable"])
    side_valves_side_1_result: Optional[str] = Field(None, examples=["pass"])
    side_valves_side_2_result: Optional[str] = Field(None, examples=["pass"])
    center_valve_result: Optional[str] = Field(None, examples=["pass"])
    lid_gasket_result: Optional[str] = Field(None, examples=["pass"])
    safety_valve_type: Optional[str] = Field(None, examples=["PV-01"])
    safety_valve_number: Optional[str] = Field(None, examples=["PV-12345"])
    grounding_result: Optional[str] = Field(None, examples=["pass"])
    utt_protocol_number: Optional[str] = Field(None, examples=["UTT-2026-001"])
    rubber_protocol_number: Optional[str] = Field(None, examples=["GUM-2026-001"])
    measured_wall_thickness_front_mm: Optional[str] = Field(None, examples=["6.2"])
    measured_wall_thickness_shell_mm: Optional[str] = Field(None, examples=["6.4"])
    measuring_device_number: Optional[str] = Field(None, examples=["MER-123"])
    calibration_valid_until: Optional[str] = Field(None, examples=["12/2026"])
    test_duration: Optional[str] = Field(None, examples=["30 min"])
    capacity_liters: Optional[int] = Field(None, ge=0, examples=[85000])
    cargo_substances: Optional[str] = Field(None, examples=["UN 1202, motorová nafta"])
    special_provisions: Optional[str] = Field(None, examples=["TU15, TE22"])
    tank_plate_stamp: Optional[str] = Field(None, examples=["Z 05/2026"])
    next_inspection: Optional[str] = Field(None, examples=["05/2029"])
    inspection_place: str = Field(..., examples=["Bratislava"])
    inspection_date: date = Field(..., examples=["2026-05-08"])
    inspector_name: str = Field(..., examples=["Ing. Ján Kontrolór"])
    result: str = Field("pass", pattern="^(pass|fail)$", examples=["pass"])
    remarks: Optional[str] = Field(None, examples=["Bez zistených nedostatkov."])
    extraordinary_inspection_reason: Optional[str] = Field(None, examples=[""])
    supplier_device_owner: Optional[str] = Field(None, examples=[""])
    supplier_device_type: Optional[str] = Field(None, examples=[""])
    supplier_device_serial_number: Optional[str] = Field(None, examples=[""])
    supplier_calibration_validity: Optional[str] = Field(None, examples=[""])
    supplier_calibration_company: Optional[str] = Field(None, examples=[""])
    supplier_snas_registration_number: Optional[str] = Field(None, examples=[""])
    supplier_other_findings: Optional[str] = Field(None, examples=[""])


class Inspection(InspectionCreate):
    id: int
    created_at: str


class InspectionResponse(BaseModel):
    inspection: Inspection
    json_path: str
    initial_record_docx_path: Optional[str] = None
    initial_record_docx_url: Optional[str] = None
    certificate_docx_path: Optional[str] = None
    certificate_docx_url: Optional[str] = None


class InspectionImportItem(InspectionCreate):
    created_at: Optional[str] = None

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class InspectionExport(BaseModel):
    exported_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    count: int
    inspections: list[Inspection]


class InspectionImportRequest(BaseModel):
    inspections: list[InspectionImportItem]


class InspectionImportResponse(BaseModel):
    imported: int
    skipped_duplicates: int
