import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models.onboarding import (
    OnboardingSessionModel,
    SessionStatus,
)


class OnboardingRepository:
    """
    Persistence operations for onboarding sessions.

    This repository does not commit transactions.
    The caller owns the transaction boundary.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> OnboardingSessionModel | None:
        stmt = select(OnboardingSessionModel).where(
            OnboardingSessionModel.user_id == user_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create_session(
        self,
        user_id: uuid.UUID,
        initial_step: str = "WELCOME",
        temporary_data: dict[str, Any] | None = None,
    ) -> OnboardingSessionModel:
        now = datetime.now(timezone.utc)

        session_model = OnboardingSessionModel(
            user_id=user_id,
            current_step=initial_step,
            status=SessionStatus.IN_PROGRESS,
            temporary_data=temporary_data or {},
            created_at=now,
            updated_at=now,
        )

        self.session.add(session_model)

        await self.session.flush()

        return session_model

    async def update_step_data(
        self,
        session_id: uuid.UUID,
        current_step: str,
        temporary_data: dict[str, Any] | None = None,
    ) -> OnboardingSessionModel | None:
        stmt = select(OnboardingSessionModel).where(
            OnboardingSessionModel.id == session_id
        )

        result = await self.session.execute(stmt)

        session_model = result.scalar_one_or_none()

        if session_model is None:
            return None

        session_model.current_step = current_step

        if temporary_data is not None:
            current_data = dict(
                session_model.temporary_data or {}
            )

            current_data.update(temporary_data)

            session_model.temporary_data = current_data

        session_model.updated_at = datetime.now(timezone.utc)

        return session_model

    async def complete_session(
        self,
        session_id: uuid.UUID,
    ) -> OnboardingSessionModel | None:
        stmt = select(OnboardingSessionModel).where(
            OnboardingSessionModel.id == session_id
        )

        result = await self.session.execute(stmt)

        session_model = result.scalar_one_or_none()

        if session_model is None:
            return None

        session_model.status = SessionStatus.COMPLETED
        session_model.current_step = "COMPLETED"
        session_model.updated_at = datetime.now(timezone.utc)

        return session_model