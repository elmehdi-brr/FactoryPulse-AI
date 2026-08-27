import pytest
from pydantic import ValidationError

from app.schemas.maintenance_record import (
    MaintenanceRecordCreate,
    MaintenanceRecordUpdate,
)


def test_create_accepts_preventive_maintenance() -> None:
    record = MaintenanceRecordCreate(
        machine_id=1,
        maintenance_type="preventive",
        description="Scheduled inspection",
        status="planned",
    )

    assert record.maintenance_type == "preventive"
    assert record.status == "planned"


def test_create_accepts_corrective_verified_maintenance() -> None:
    record = MaintenanceRecordCreate(
        machine_id=1,
        maintenance_type="corrective",
        description="Motor repaired and verified",
        status="verified",
    )

    assert record.maintenance_type == "corrective"
    assert record.status == "verified"


def test_create_rejects_invalid_maintenance_type() -> None:
    with pytest.raises(ValidationError):
        MaintenanceRecordCreate(
            machine_id=1,
            maintenance_type="inspection",
            description="Invalid maintenance type",
        )


def test_create_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        MaintenanceRecordCreate(
            machine_id=1,
            maintenance_type="corrective",
            description="Invalid maintenance status",
            status="unknown",
        )


def test_update_rejects_invalid_vocabulary() -> None:
    with pytest.raises(ValidationError):
        MaintenanceRecordUpdate(
            maintenance_type="emergency",
        )

    with pytest.raises(ValidationError):
        MaintenanceRecordUpdate(
            status="done",
        )