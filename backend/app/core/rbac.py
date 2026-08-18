from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    TECHNICIAN = "technician"
    OPERATOR = "operator"