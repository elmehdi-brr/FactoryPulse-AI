from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, TECHNICAL_WRITE_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.maintenance_record import (
    MaintenanceRecordCreate,
    MaintenanceRecordResponse,
    MaintenanceRecordUpdate,
)
from app.services.alert_service import get_alert_by_id
from app.services.machine_service import get_machine_by_id
from app.services.maintenance_record_service import (
    create_maintenance_record,
    get_maintenance_record_by_id,
    get_maintenance_records,
    get_maintenance_records_by_machine,
    update_maintenance_record,
)
from app.services.sensor_service import get_sensor_by_id
from app.services.user_service import get_user_by_id


router = APIRouter(
    tags=["Maintenance Records"],
)


@router.post(
    "/maintenance-records",
    response_model=MaintenanceRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_maintenance_record_endpoint(
    maintenance_data: MaintenanceRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*TECHNICAL_WRITE_ROLES)),
) -> MaintenanceRecordResponse:
    machine = await get_machine_by_id(db, maintenance_data.machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    if maintenance_data.alert_id is not None:
        alert = await get_alert_by_id(db, maintenance_data.alert_id)

        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        sensor = await get_sensor_by_id(db, alert.sensor_id)

        if sensor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sensor not found",
            )

        if sensor.machine_id != maintenance_data.machine_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert does not belong to the specified machine",
            )

    if maintenance_data.performed_by_user_id is not None:
        user = await get_user_by_id(
            db,
            maintenance_data.performed_by_user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    return await create_maintenance_record(db, maintenance_data)


@router.get(
    "/maintenance-records",
    response_model=list[MaintenanceRecordResponse],
)
async def get_maintenance_records_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[MaintenanceRecordResponse]:
    return await get_maintenance_records(db)


@router.get(
    "/maintenance-records/{record_id}",
    response_model=MaintenanceRecordResponse,
)
async def get_maintenance_record_endpoint(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> MaintenanceRecordResponse:
    record = await get_maintenance_record_by_id(db, record_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    return record


@router.get(
    "/machines/{machine_id}/maintenance-records",
    response_model=list[MaintenanceRecordResponse],
)
async def get_machine_maintenance_records_endpoint(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[MaintenanceRecordResponse]:
    machine = await get_machine_by_id(db, machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return await get_maintenance_records_by_machine(db, machine_id)


@router.patch(
    "/maintenance-records/{record_id}",
    response_model=MaintenanceRecordResponse,
)
async def update_maintenance_record_endpoint(
    record_id: int,
    maintenance_data: MaintenanceRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*TECHNICAL_WRITE_ROLES)),
) -> MaintenanceRecordResponse:
    record = await get_maintenance_record_by_id(db, record_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found",
        )

    if maintenance_data.alert_id is not None:
        alert = await get_alert_by_id(db, maintenance_data.alert_id)

        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        sensor = await get_sensor_by_id(db, alert.sensor_id)

        if sensor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sensor not found",
            )

        if sensor.machine_id != record.machine_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert does not belong to the maintenance record machine",
            )

    if maintenance_data.performed_by_user_id is not None:
        user = await get_user_by_id(
            db,
            maintenance_data.performed_by_user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    return await update_maintenance_record(
        db,
        record,
        maintenance_data,
    )