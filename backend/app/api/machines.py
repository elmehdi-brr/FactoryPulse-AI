from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, ASSET_WRITE_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.machine import MachineCreate, MachineResponse, MachineUpdate
from app.services.machine_service import (
    create_machine,
    delete_machine,
    get_machine_by_id,
    get_machines,
    update_machine,
)


router = APIRouter(
    prefix="/machines",
    tags=["Machines"],
)


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_machine_endpoint(
    machine_data: MachineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ASSET_WRITE_ROLES)),
) -> MachineResponse:
    return await create_machine(db, machine_data)


@router.get(
    "",
    response_model=list[MachineResponse],
)
async def get_machines_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[MachineResponse]:
    return await get_machines(db)


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
async def get_machine_endpoint(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> MachineResponse:
    machine = await get_machine_by_id(db, machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return machine


@router.patch(
    "/{machine_id}",
    response_model=MachineResponse,
)
async def update_machine_endpoint(
    machine_id: int,
    machine_data: MachineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ASSET_WRITE_ROLES)),
) -> MachineResponse:
    machine = await get_machine_by_id(db, machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return await update_machine(db, machine, machine_data)


@router.delete(
    "/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_machine_endpoint(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> None:
    machine = await get_machine_by_id(db, machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    await delete_machine(db, machine)