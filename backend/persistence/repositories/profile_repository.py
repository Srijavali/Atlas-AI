import uuid
from datetime import datetime, time, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models.profile import UserProfileModel


class ProfileRepository:
    """
    Persistence operations for user profiles.

    This repository does not commit transactions.
    The caller owns the transaction boundary.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> UserProfileModel | None:
        stmt = select(UserProfileModel).where(
            UserProfileModel.user_id == user_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create_or_update_profile(
        self,
        user_id: uuid.UUID,
        interests: Any | None = None,
        market_preferences: Any | None = None,
        tracked_entities: Any | None = None,
        briefing_enabled: bool = False,
        briefing_time: time | None = None,
        timezone_str: str | None = None,
    ) -> UserProfileModel:
        profile = await self.get_by_user_id(user_id)

        now = datetime.now(timezone.utc)

        if profile is None:
            profile = UserProfileModel(
                user_id=user_id,
                interests=interests,
                market_preferences=market_preferences,
                tracked_entities=tracked_entities,
                briefing_enabled=briefing_enabled,
                briefing_time=briefing_time,
                timezone=timezone_str,
                created_at=now,
                updated_at=now,
            )

            self.session.add(profile)

        else:
            if interests is not None:
                profile.interests = interests

            if market_preferences is not None:
                profile.market_preferences = market_preferences

            if tracked_entities is not None:
                profile.tracked_entities = tracked_entities

            profile.briefing_enabled = briefing_enabled

            if briefing_time is not None:
                profile.briefing_time = briefing_time

            if timezone_str is not None:
                profile.timezone = timezone_str

            profile.updated_at = now

        await self.session.flush()

        return profile