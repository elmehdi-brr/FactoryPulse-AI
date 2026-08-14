from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("alerts.id"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    channel: Mapped[str] = mapped_column(
        String(30),
        default="in_app",
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="notifications")
    alert: Mapped["Alert | None"] = relationship(back_populates="notifications")