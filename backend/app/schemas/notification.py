from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    user_id: int
    alert_id: int | None = None
    title: str
    message: str
    channel: str = "in_app"
    is_read: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    is_read: bool | None = None


class NotificationResponse(NotificationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)