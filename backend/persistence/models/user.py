import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, BigInteger, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.persistence.database import Base

class OnboardingStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    telegram_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    onboarding_status: Mapped[OnboardingStatus] = mapped_column(
        SQLEnum(OnboardingStatus, name="onboarding_status_enum", native_enum=False),
        nullable=False,
        default=OnboardingStatus.NOT_STARTED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    profile = relationship("UserProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    onboarding_session = relationship("OnboardingSessionModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
