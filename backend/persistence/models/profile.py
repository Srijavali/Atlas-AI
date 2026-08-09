
import uuid
from datetime import datetime, time, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.persistence.database import Base


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # USER CONTEXT
    # ---------------------------------------------------------

    role: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    interests: Mapped[list | dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Financial / market preferences.
    market_preferences: Mapped[list | dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Companies, stocks, sectors, markets, people, etc.
    tracked_entities: Mapped[list | dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # What type of information the user wants Atlas
    # to prioritize in research / briefings.
    insight_preferences: Mapped[list | dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # What Atlas should proactively monitor / alert on.
    alert_preferences: Mapped[list | dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ---------------------------------------------------------
    # BRIEFING PREFERENCES
    # ---------------------------------------------------------

    briefing_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    briefing_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ---------------------------------------------------------
    # TIMESTAMPS
    # ---------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship(
        "UserModel",
        back_populates="profile",
    )

