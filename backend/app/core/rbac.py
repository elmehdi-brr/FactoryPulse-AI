from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    TECHNICIAN = "technician"
    OPERATOR = "operator"


ALL_ROLES = (
    RoleName.ADMIN,
    RoleName.MANAGER,
    RoleName.TECHNICIAN,
    RoleName.OPERATOR,
)

MANAGEMENT_ROLES = (
    RoleName.ADMIN,
    RoleName.MANAGER,
)

ASSET_WRITE_ROLES = (
    RoleName.ADMIN,
    RoleName.MANAGER,
    RoleName.TECHNICIAN,
)

TECHNICAL_WRITE_ROLES = (
    RoleName.ADMIN,
    RoleName.TECHNICIAN,
)

READING_WRITE_ROLES = (
    RoleName.ADMIN,
    RoleName.TECHNICIAN,
    RoleName.OPERATOR,
)