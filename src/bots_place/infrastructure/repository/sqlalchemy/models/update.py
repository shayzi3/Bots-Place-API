from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Update(Base):
    __tablename__ = "updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    sender_bot_id: Mapped[int | None] = mapped_column(
        ForeignKey("bots.id", ondelete="SET NULL"), index=True
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(
        String(20)
    )  # src.bots_place.domain.entities.update.UpdateTypeEnum
    update_from: Mapped[str] = mapped_column(
        String(10)
    )  # src.bots_place.domain.entities.update.UpdateFromEnum
    payload: Mapped[dict] = mapped_column(JSON)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
