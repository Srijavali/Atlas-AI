import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models.user import OnboardingStatus, UserModel


class UserRepository:
    """
    Persistence operations for Atlas users.

    Important:
    This repository does NOT commit transactions.
    Transaction ownership belongs to the application/service layer.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> UserModel | None:
        stmt = select(UserModel).where(
            UserModel.telegram_user_id == telegram_user_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        user_id: uuid.UUID,
    ) -> UserModel | None:
        stmt = select(UserModel).where(
            UserModel.id == user_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_user_id: int,
        telegram_username: str | None = None,
        display_name: str | None = None,
    ) -> UserModel:
        now = datetime.now(timezone.utc)

        user = UserModel(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            display_name=display_name,
            onboarding_status=OnboardingStatus.NOT_STARTED,
            created_at=now,
            last_seen_at=now,
        )

        self.session.add(user)

        # Flush so SQLAlchemy sends the INSERT to PostgreSQL
        # without committing the surrounding transaction.
        await self.session.flush()

        return user

    async def update_last_seen(
        self,
        user_id: uuid.UUID,
    ) -> UserModel | None:
        user = await self.get_by_id(user_id)

        if user is None:
            return None

        user.last_seen_at = datetime.now(timezone.utc)

        return user

    async def update_onboarding_status(
        self,
        user_id: uuid.UUID,
        status: OnboardingStatus,
        display_name: str | None = None,
    ) -> UserModel | None:
        user = await self.get_by_id(user_id)

        if user is None:
            return None

        user.onboarding_status = status

        if display_name is not None:
            user.display_name = display_name

        if status == OnboardingStatus.COMPLETED:
            user.onboarding_completed_at = datetime.now(timezone.utc)

        return user

    async def count_users(self) -> int:
        stmt = select(func.count()).select_from(UserModel)

        result = await self.session.execute(stmt)

        return result.scalar_one()