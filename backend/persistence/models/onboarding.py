import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.persistence.database import Base

class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class OnboardingSessionModel(Base):
    __tablename__ = "onboarding_sessions"

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
    current_step: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus, name="session_status_enum", native_enum=False),
        nullable=False,
        default=SessionStatus.IN_PROGRESS
    )
    temporary_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
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

    user = relationship("UserModel", back_populates="onboarding_session")
