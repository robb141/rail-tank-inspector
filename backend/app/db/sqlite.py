import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import DB_PATH, ensure_storage_dirs
from app.models import Inspection, InspectionCreate, InspectionImportItem


def get_connection() -> sqlite3.Connection:
    ensure_storage_dirs()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_number TEXT NOT NULL,
                holder_name TEXT NOT NULL,
                tank_identification TEXT NOT NULL,
                result TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def create_inspection_with_created_at(
    payload: InspectionCreate,
    created_at: str | None = None,
) -> Inspection:
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    payload_dict = payload.model_dump(mode="json")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO inspections (
                certificate_number,
                holder_name,
                tank_identification,
                result,
                payload_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.certificate_number,
                payload.holder_name,
                payload.tank_identification,
                payload.result,
                json.dumps(payload_dict, ensure_ascii=False, indent=2),
                created_at,
            ),
        )
        inspection_id = int(cursor.lastrowid)

    return Inspection(id=inspection_id, created_at=created_at, **payload_dict)


def create_inspection(payload: InspectionCreate) -> Inspection:
    return create_inspection_with_created_at(payload)


def update_inspection(inspection_id: int, payload: InspectionCreate) -> Inspection | None:
    existing = get_inspection(inspection_id)
    if existing is None:
        return None

    payload_dict = payload.model_dump(mode="json")
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE inspections
            SET certificate_number = ?,
                holder_name = ?,
                tank_identification = ?,
                result = ?,
                payload_json = ?
            WHERE id = ?
            """,
            (
                payload.certificate_number,
                payload.holder_name,
                payload.tank_identification,
                payload.result,
                json.dumps(payload_dict, ensure_ascii=False, indent=2),
                inspection_id,
            ),
        )

    return Inspection(id=inspection_id, created_at=existing.created_at, **payload_dict)


def list_inspections() -> list[Inspection]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, payload_json, created_at FROM inspections ORDER BY id DESC"
        ).fetchall()

    inspections: list[Inspection] = []
    for row in rows:
        payload: dict[str, Any] = json.loads(row["payload_json"])
        inspections.append(Inspection(id=row["id"], created_at=row["created_at"], **payload))
    return inspections


def get_inspection(inspection_id: int) -> Inspection | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, payload_json, created_at FROM inspections WHERE id = ?",
            (inspection_id,),
        ).fetchone()

    if row is None:
        return None

    payload: dict[str, Any] = json.loads(row["payload_json"])
    return Inspection(id=row["id"], created_at=row["created_at"], **payload)


def inspection_exists(payload: InspectionCreate) -> bool:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT payload_json FROM inspections WHERE certificate_number = ? AND tank_identification = ?",
            (payload.certificate_number, payload.tank_identification),
        ).fetchall()

    for row in rows:
        existing_payload: dict[str, Any] = json.loads(row["payload_json"])
        if existing_payload.get("inspection_date") == payload.model_dump(mode="json").get("inspection_date"):
            return True
    return False


def import_inspections(items: list[InspectionImportItem]) -> tuple[int, int]:
    imported = 0
    skipped_duplicates = 0

    for item in items:
        payload = InspectionCreate.model_validate(item.model_dump(exclude={"created_at"}))
        if inspection_exists(payload):
            skipped_duplicates += 1
            continue

        create_inspection_with_created_at(payload, item.created_at)
        imported += 1

    return imported, skipped_duplicates
