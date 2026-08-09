
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
    async with AsyncSessionFactory() as session:
        user_repository = UserRepository(session)
        onboarding_repository = OnboardingRepository(session)
        profile_repository = ProfileRepository(session)

        # ---------------------------------------------------------
        # CREATE USER
        # ---------------------------------------------------------

        user = await user_repository.create_user(
            telegram_user_id=int(time.time() * 1000),
            telegram_username="atlas_test_user",
            display_name=None,
        )

        service = OnboardingService(
            onboarding_repository=onboarding_repository,
            user_repository=user_repository,
            profile_repository=profile_repository,
        )

        # ---------------------------------------------------------
        # START ONBOARDING
        # ---------------------------------------------------------

        result = await service.start(user.id)

        assert result.step == "WELCOME"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "WELCOME"
        assert onboarding_session.status == SessionStatus.IN_PROGRESS

        # ---------------------------------------------------------
        # WELCOME -> ASK_NAME
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # ASK_NAME -> ASK_TIMEZONE
        # ---------------------------------------------------------

        result = await service.handle_response(
            session=onboarding_session,
            response="Sri",
        )

        assert result.step == "ASK_TIMEZONE"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_TIMEZONE"

        assert (
            onboarding_session.temporary_data["display_name"]
            == "Sri"
        )

        # ---------------------------------------------------------
        # ASK_TIMEZONE -> ASK_INTERESTS
        # ---------------------------------------------------------

        result = await service.handle_response(
            session=onboarding_session,
            response="Asia/Kolkata",
        )

        assert result.step == "ASK_INTERESTS"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_INTERESTS"

        assert (
            onboarding_session.temporary_data["timezone"]
            == "Asia/Kolkata"
        )

        # ---------------------------------------------------------
        # ASK_INTERESTS -> ASK_BRIEFING
        # ---------------------------------------------------------

        result = await service.handle_response(
            session=onboarding_session,
            response="AI, technology, startups",
        )

        assert result.step == "ASK_BRIEFING"
        assert result.completed is False

        onboarding_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert onboarding_session is not None
        assert onboarding_session.current_step == "ASK_BRIEFING"

        assert onboarding_session.temporary_data["interests"] == [
            "AI",
            "technology",
            "startups",
        ]

        # ---------------------------------------------------------
        # ASK_BRIEFING -> COMPLETED
        # ---------------------------------------------------------

        result = await service.handle_response(
            session=onboarding_session,
            response="yes",
        )

        assert result.step == "COMPLETED"
        assert result.completed is True

        # ---------------------------------------------------------
        # VERIFY ONBOARDING SESSION
        # ---------------------------------------------------------

        completed_session = (
            await onboarding_repository.get_by_user_id(user.id)
        )

        assert completed_session is not None
        assert completed_session.current_step == "COMPLETED"
        assert completed_session.status == SessionStatus.COMPLETED

        assert (
            completed_session.temporary_data["display_name"]
            == "Sri"
        )

        assert (
            completed_session.temporary_data["timezone"]
            == "Asia/Kolkata"
        )

        assert completed_session.temporary_data["interests"] == [
            "AI",
            "technology",
            "startups",
        ]


        # ---------------------------------------------------------
        # VERIFY USER
        # ---------------------------------------------------------

        persisted_user = await user_repository.get_by_id(user.id)

        assert persisted_user is not None

        assert (
            persisted_user.onboarding_status
            == OnboardingStatus.COMPLETED
        )

        assert persisted_user.display_name == "Sri"

        assert persisted_user.onboarding_completed_at is not None

        # ---------------------------------------------------------
        # VERIFY PROFILE
        # ---------------------------------------------------------

        profile = await profile_repository.get_by_user_id(user.id)

        assert profile is not None

        assert profile.timezone == "Asia/Kolkata"

        assert profile.briefing_enabled is True

        assert profile.interests == [
            "AI",
            "technology",
            "startups",
        ]

        # ---------------------------------------------------------
        # ROLLBACK TEST TRANSACTION
        # ---------------------------------------------------------

        await session.rollback()

