from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


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
    test_pressure: Optional[str] = Field(None, examples=["4 bar"])
    working_pressure: Optional[str] = Field(None, examples=["3 bar"])
    calculation_pressure: Optional[str] = Field(None, examples=["4.5 bar"])
    safety_valve_pressure: Optional[str] = Field(None, examples=["3.3 bar"])
    vacuum_valve_pressure: Optional[str] = Field(None, examples=["-0.21 bar"])
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
