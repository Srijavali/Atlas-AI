
import time

import pytest

from backend.modules.preferences.schemas import PreferenceChange
from backend.modules.preferences.service import PreferenceService
from backend.persistence.database import AsyncSessionFactory
from backend.persistence.repositories.profile_repository import (
    ProfileRepository,
)
from backend.persistence.repositories.user_repository import (
    UserRepository,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_preference_change_persists_end_to_end():
    """
    Verify the complete preference update flow:

        PreferenceService
            ↓
        ProfileRepository
            ↓
        PostgreSQL
            ↓
        Updated profile

    The test also verifies that unrelated preferences remain unchanged.
    """

    async with AsyncSessionFactory() as session:
        user_repository = UserRepository(session)
        profile_repository = ProfileRepository(session)

        # ---------------------------------------------------------
        # CREATE USER
        # ---------------------------------------------------------

        user = await user_repository.create_user(
            telegram_user_id=int(time.time() * 1000),
            telegram_username="atlas_preferences_test",
            display_name="Sri",
        )

        # ---------------------------------------------------------
        # CREATE INITIAL PROFILE
        # ---------------------------------------------------------

        profile = await profile_repository.create_or_update_profile(
            user_id=user.id,
            role="Analyst",
            interests=[
                "AI",
                "technology",
            ],
            market_preferences=[
                "Stocks",
                "ETFs",
            ],
            tracked_entities=[
                "NVIDIA",
                "Microsoft",
            ],
            insight_preferences=[
                "Earnings",
                "Company news",
            ],
            alert_preferences=[
                "Large market moves",
            ],
            briefing_enabled=True,
            briefing_time=None,
            timezone_str="Asia/Kolkata",
        )

        assert profile is not None
        assert profile.interests == [
            "AI",
            "technology",
        ]

        assert profile.briefing_enabled is True
        assert profile.timezone == "Asia/Kolkata"

        # ---------------------------------------------------------
        # CREATE SERVICE
        # ---------------------------------------------------------

        service = PreferenceService(
            profile_repository=profile_repository,
        )

        # ---------------------------------------------------------
        # LOAD CURRENT PROFILE
        # ---------------------------------------------------------

        current_profile = (
            await profile_repository.get_by_user_id(user.id)
        )

        assert current_profile is not None

        assert current_profile.interests == [
            "AI",
            "technology",
        ]

        # ---------------------------------------------------------
        # USER REQUESTS INTEREST CHANGE
        # ---------------------------------------------------------

        result = await service.handle_response(
            user_id=user.id,
            profile=current_profile,
            step="EDIT_INTERESTS",
            response="finance, markets",
        )

        assert result.step == "CONFIRM_CHANGE"
        assert result.completed is False

        assert "AI" in result.message
        assert "technology" in result.message
        assert "finance" in result.message
        assert "markets" in result.message

        # ---------------------------------------------------------
        # IMPORTANT:
        # DATABASE MUST NOT CHANGE BEFORE CONFIRMATION
        # ---------------------------------------------------------

        unchanged_profile = (
            await profile_repository.get_by_user_id(user.id)
        )

        assert unchanged_profile is not None

        assert unchanged_profile.interests == [
            "AI",
            "technology",
        ]

        # ---------------------------------------------------------
        # EXTRACT THE PROPOSED CHANGE
        #
        # In the real conversational layer this pending change
        # will be retained between turns.
        # ---------------------------------------------------------

        pending_change = PreferenceChange(
            field="interests",
            old_value=[
                "AI",
                "technology",
            ],
            new_value=[
                "finance",
                "markets",
            ],
        )

        # ---------------------------------------------------------
        # USER CONFIRMS
        # ---------------------------------------------------------

        result = await service.handle_response(
            user_id=user.id,
            profile=unchanged_profile,
            step="CONFIRM_CHANGE",
            response="yes",
            pending_change=pending_change,
        )

        assert result.step == "UPDATED"
        assert result.completed is True

        # ---------------------------------------------------------
        # RELOAD PROFILE FROM DATABASE
        # ---------------------------------------------------------

        updated_profile = (
            await profile_repository.get_by_user_id(user.id)
        )

        assert updated_profile is not None

        # ---------------------------------------------------------
        # VERIFY CHANGED PREFERENCE
        # ---------------------------------------------------------

        assert updated_profile.interests == [
            "finance",
            "markets",
        ]

        # ---------------------------------------------------------
        # VERIFY UNRELATED PREFERENCES WERE PRESERVED
        # ---------------------------------------------------------

        assert updated_profile.role == "Analyst"

        assert updated_profile.market_preferences == [
            "Stocks",
            "ETFs",
        ]

        assert updated_profile.tracked_entities == [
            "NVIDIA",
            "Microsoft",
        ]

        assert updated_profile.insight_preferences == [
            "Earnings",
            "Company news",
        ]

        assert updated_profile.alert_preferences == [
            "Large market moves",
        ]

        assert updated_profile.briefing_enabled is True

        assert updated_profile.timezone == "Asia/Kolkata"

        # ---------------------------------------------------------
        # USER CANCEL FLOW
        #
        # Make another proposed change and verify that saying
        # "no" does NOT modify PostgreSQL.
        # ---------------------------------------------------------

        cancel_change = PreferenceChange(
            field="interests",
            old_value=[
                "finance",
                "markets",
            ],
            new_value=[
                "crypto",
                "forex",
            ],
        )

        result = await service.handle_response(
            user_id=user.id,
            profile=updated_profile,
            step="CONFIRM_CHANGE",
            response="no",
            pending_change=cancel_change,
        )

        assert result.step == "SELECT_PREFERENCE"
        assert result.completed is False

        # ---------------------------------------------------------
        # VERIFY DATABASE DID NOT CHANGE AFTER CANCELLATION
        # ---------------------------------------------------------

        final_profile = (
            await profile_repository.get_by_user_id(user.id)
        )

        assert final_profile is not None

        assert final_profile.interests == [
            "finance",
            "markets",
        ]

        # ---------------------------------------------------------
        # ROLLBACK TEST TRANSACTION
        # ---------------------------------------------------------

        await session.rollback()
