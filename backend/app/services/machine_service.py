from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import Machine
from app.schemas.machine import MachineCreate, MachineUpdate


async def create_machine(
    db: AsyncSession,
    machine_data: MachineCreate,
) -> Machine:
    machine = Machine(**machine_data.model_dump())

    db.add(machine)
    await db.commit()
    await db.refresh(machine)

    return machine


async def get_machine_by_id(
    db: AsyncSession,
    machine_id: int,
) -> Machine | None:
    result = await db.execute(
        select(Machine).where(Machine.id == machine_id)
    )

    return result.scalar_one_or_none()


async def get_machines(
    db: AsyncSession,
) -> list[Machine]:
    result = await db.execute(
        select(Machine).order_by(Machine.id)
    )

    return list(result.scalars().all())


async def update_machine(
    db: AsyncSession,
    machine: Machine,
    machine_data: MachineUpdate,
) -> Machine:
    update_data = machine_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(machine, field, value)

    await db.commit()
    await db.refresh(machine)

    return machine


async def delete_machine(
    db: AsyncSession,
    machine: Machine,
) -> None:
    await db.delete(machine)
    await db.commit()