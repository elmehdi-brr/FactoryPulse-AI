from .alert import AlertCreate, AlertResponse, AlertUpdate
from .machine import MachineCreate, MachineResponse, MachineUpdate
from .maintenance_record import (
    MaintenanceRecordCreate,
    MaintenanceRecordResponse,
    MaintenanceRecordUpdate,
)
from .notification import NotificationCreate, NotificationResponse, NotificationUpdate
from .prediction import PredictionCreate, PredictionResponse
from .role import RoleCreate, RoleResponse, RoleUpdate
from .sensor import SensorCreate, SensorResponse, SensorUpdate
from .sensor_reading import SensorReadingCreate, SensorReadingResponse
from .user import UserCreate, UserResponse, UserUpdate
from .auth import TokenResponse

__all__ = [
    "AlertCreate",
    "AlertResponse",
    "AlertUpdate",
    "MachineCreate",
    "MachineResponse",
    "MachineUpdate",
    "MaintenanceRecordCreate",
    "MaintenanceRecordResponse",
    "MaintenanceRecordUpdate",
    "NotificationCreate",
    "NotificationResponse",
    "NotificationUpdate",
    "PredictionCreate",
    "PredictionResponse",
    "RoleCreate",
    "RoleResponse",
    "RoleUpdate",
    "SensorCreate",
    "SensorResponse",
    "SensorUpdate",
    "SensorReadingCreate",
    "SensorReadingResponse",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "TokenResponse",
]