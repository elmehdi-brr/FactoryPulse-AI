import asyncio

from sqlalchemy import select

from app.core.rbac import RoleName
from app.db.session import AsyncSessionLocal
from app.models.role import Role
from app.models.user import User


ROLE_DEFINITIONS = {
    RoleName.ADMIN: "Full administrative access to FactoryPulse.",
    RoleName.MANAGER: "Management access to industrial operations and reporting.",
    RoleName.TECHNICIAN: "Maintenance and technical operational access.",
    RoleName.OPERATOR: "Day-to-day industrial monitoring and operational access.",
}


async def seed_rbac() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Role))
        existing_roles = {
            role.name: role
            for role in result.scalars().all()
        }

        for role_name, description in ROLE_DEFINITIONS.items():
            if role_name.value not in existing_roles:
                db.add(
                    Role(
                        name=role_name.value,
                        description=description,
                    )
                )

        await db.flush()

        operator_role_result = await db.execute(
            select(Role).where(
                Role.name == RoleName.OPERATOR.value
            )
        )
        operator_role = operator_role_result.scalar_one()

        user_result = await db.execute(
            select(User).where(
                User.email == "operator@factorypulse.local"
            )
        )
        operator_user = user_result.scalar_one_or_none()

        if operator_user is not None and operator_user.role_id is None:
            operator_user.role_id = operator_role.id

        await db.commit()

        print("RBAC roles seeded successfully.")

        if operator_user is not None:
            print(
                f"Development user role: "
                f"{operator_user.email} -> {RoleName.OPERATOR.value}"
            )


if __name__ == "__main__":
    asyncio.run(seed_rbac())