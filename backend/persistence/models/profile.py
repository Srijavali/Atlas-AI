import uuid
from datetime import datetime, time, timezone
from sqlalchemy import ForeignKey, Boolean, Time, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.persistence.database import Base

class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    interests: Mapped[dict | list | None] = mapped_column(
        JSONB,
        nullable=True
    )
    market_preferences: Mapped[dict | list | None] = mapped_column(
        JSONB,
        nullable=True
    )
    tracked_entities: Mapped[dict | list | None] = mapped_column(
        JSONB,
        nullable=True
    )
    briefing_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    briefing_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )
    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = relationship("UserModel", back_populates="profile")
