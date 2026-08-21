import time

import pytest

from backend.modules.onboarding.service import OnboardingService
from backend.persistence.database import AsyncSessionFactory
from backend.persistence.models.onboarding import SessionStatus
from backend.persistence.models.user import OnboardingStatus
from backend.persistence.repositories.onboarding_repository import (
    OnboardingRepository,
)
from backend.persistence.repositories.profile_repository import (
    ProfileRepository,
)
from backend.persistence.repositories.user_repository import (
    UserRepository,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_onboarding_persists_end_to_end():
    """
    Verify the complete first-interaction onboarding flow.

    Flow:

        WELCOME
        -> ASK_NAME
        -> ASK_INTERESTS
        -> ASK_WATCHLIST
        -> ASK_DAILY_BRIEFING
        -> ASK_BRIEFING_TIME
        -> ASK_TIMEZONE
        -> CONFIRM
        -> COMPLETED

    The test verifies that the onboarding data collected by the
    current Atlas onboarding flow is correctly persisted to PostgreSQL.
    """

    async with AsyncSessionFactory() as session:

        user_repository = UserRepository(session)
        onboarding_repository = OnboardingRepository(session)
        profile_repository = ProfileRepository(session)

        # =========================================================
        # CREATE USER
        # =========================================================

        user = await user_repository.create_user(
            telegram_user_id=int(time.time() * 1000),
            telegram_username="atlas_onboarding_test",
            display_name=None,
        )

        service = OnboardingService(
            onboarding_repository=onboarding_repository,
            user_repository=user_repository,
            profile_repository=profile_repository,
        )

        # =========================================================
        # START ONBOARDING
        # =========================================================

        result = await service.start(user.id)

        assert result.step == "WELCOME"
        assert result.completed is False
        assert "Atlas" in result.message

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "WELCOME"
        assert onboarding_session.status == SessionStatus.IN_PROGRESS

        # =========================================================
        # WELCOME -> ASK_NAME
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="Hi",
        )

        assert result.step == "ASK_NAME"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_NAME"

        # =========================================================
        # ASK_NAME -> ASK_INTERESTS
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="Sri",
        )

        assert result.step == "ASK_INTERESTS"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_INTERESTS"

        assert (
            onboarding_session.temporary_data["display_name"]
            == "Sri"
        )

        # =========================================================
        # ASK_INTERESTS -> ASK_WATCHLIST
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="AI, technology, startups",
        )

        assert result.step == "ASK_WATCHLIST"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_WATCHLIST"

        assert onboarding_session.temporary_data["interests"] == [
            "AI",
            "technology",
            "startups",
        ]

        # =========================================================
        # ASK_WATCHLIST -> ASK_DAILY_BRIEFING
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="NVIDIA, Microsoft, TCS",
        )

        assert result.step == "ASK_DAILY_BRIEFING"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_DAILY_BRIEFING"

        assert onboarding_session.temporary_data[
            "tracked_entities"
        ] == [
            "NVIDIA",
            "Microsoft",
            "TCS",
        ]

        # =========================================================
        # ASK_DAILY_BRIEFING -> ASK_BRIEFING_TIME
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="yes",
        )

        assert result.step == "ASK_BRIEFING_TIME"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_BRIEFING_TIME"

        assert (
            onboarding_session.temporary_data[
                "briefing_enabled"
            ]
            is True
        )

        # =========================================================
        # ASK_BRIEFING_TIME -> ASK_TIMEZONE
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="8:00 AM",
        )

        assert result.step == "ASK_TIMEZONE"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_TIMEZONE"

        assert (
            onboarding_session.temporary_data["briefing_time"]
            == "08:00:00"
        )

        # =========================================================
        # ASK_TIMEZONE -> CONFIRM
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="Asia/Kolkata",
        )

        assert result.step == "CONFIRM"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "CONFIRM"

        assert (
            onboarding_session.temporary_data["timezone"]
            == "Asia/Kolkata"
        )

        # =========================================================
        # CONFIRM -> COMPLETED
        # =========================================================

        result = await service.handle_response(
            session=onboarding_session,
            response="yes",
        )

        assert result.step == "COMPLETED"
        assert result.completed is True
        assert "Atlas" in result.message
        assert "all set" in result.message.lower()

        # =========================================================
        # VERIFY ONBOARDING SESSION
        # =========================================================

        completed_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert completed_session is not None
        assert completed_session.current_step == "COMPLETED"
        assert completed_session.status == SessionStatus.COMPLETED

        temporary_data = completed_session.temporary_data

        assert temporary_data["display_name"] == "Sri"

        assert temporary_data["interests"] == [
            "AI",
            "technology",
            "startups",
        ]

        assert temporary_data["tracked_entities"] == [
            "NVIDIA",
            "Microsoft",
            "TCS",
        ]

        assert temporary_data["briefing_enabled"] is True

        assert temporary_data["briefing_time"] == "08:00:00"

        assert temporary_data["timezone"] == "Asia/Kolkata"

        # =========================================================
        # VERIFY USER PERSISTENCE
        # =========================================================

        persisted_user = await user_repository.get_by_id(user.id)

        assert persisted_user is not None

        assert (
            persisted_user.onboarding_status
            == OnboardingStatus.COMPLETED
        )

        assert persisted_user.display_name == "Sri"

        assert persisted_user.onboarding_completed_at is not None

        # =========================================================
        # VERIFY PROFILE PERSISTENCE
        # =========================================================

        profile = await profile_repository.get_by_user_id(user.id)

        assert profile is not None

        # The new onboarding intentionally does not collect role.
        assert profile.role is None

        assert profile.interests == [
            "AI",
            "technology",
            "startups",
        ]

        # These fields are no longer collected during first interaction.
        assert profile.market_preferences == []

        assert profile.tracked_entities == [
            "NVIDIA",
            "Microsoft",
            "TCS",
        ]

        assert profile.insight_preferences == []

        assert profile.alert_preferences == []

        assert profile.briefing_enabled is True

        assert profile.briefing_time is not None
        assert profile.briefing_time.hour == 8
        assert profile.briefing_time.minute == 0

        assert profile.timezone == "Asia/Kolkata"

        # =========================================================
        # ROLLBACK TEST TRANSACTION
        # =========================================================

        await session.rollback()