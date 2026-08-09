
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from backend.modules.preferences.schemas import PreferenceChange
from backend.modules.preferences.service import PreferenceService


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def profile_repository():
    repository = Mock()
    repository.get_by_user_id = AsyncMock()
    repository.create_or_update_profile = AsyncMock()
    return repository


@pytest.fixture
def service(profile_repository):
    return PreferenceService(
        profile_repository=profile_repository,
    )


@pytest.fixture
def profile():
    profile = Mock()

    profile.role = "Analyst"
    profile.interests = [
        "AI",
        "technology",
        "startups",
    ]
    profile.market_preferences = [
        "Stocks",
        "ETFs",
    ]
    profile.tracked_entities = [
        "NVIDIA",
        "Microsoft",
    ]
    profile.insight_preferences = [
        "Earnings",
        "Company news",
    ]
    profile.alert_preferences = [
        "Large market moves",
    ]
    profile.briefing_enabled = True
    profile.briefing_time = "08:00"
    profile.timezone = "Asia/Kolkata"

    return profile


# ============================================================
# START
# ============================================================


@pytest.mark.asyncio
async def test_start_shows_current_preferences(
    service,
    profile_repository,
    profile,
):
    user_id = uuid4()

    profile_repository.get_by_user_id.return_value = profile

    result = await service.start(
        user_id=user_id,
    )

    profile_repository.get_by_user_id.assert_awaited_once_with(
        user_id
    )

    assert result.step == "SELECT_PREFERENCE"
    assert result.completed is False

    assert "Analyst" in result.message
    assert "AI" in result.message
    assert "NVIDIA" in result.message
    assert "Asia/Kolkata" in result.message


@pytest.mark.asyncio
async def test_start_without_profile_returns_no_profile(
    service,
    profile_repository,
):
    user_id = uuid4()

    profile_repository.get_by_user_id.return_value = None

    result = await service.start(
        user_id=user_id,
    )

    assert result.step == "NO_PROFILE"
    assert result.completed is True

    assert "profile" in result.message.lower()


# ============================================================
# PREFERENCE SELECTION
# ============================================================


@pytest.mark.asyncio
async def test_briefing_alias_resolves_to_briefing_enabled(
    service,
    profile,
):
    user_id = uuid4()

    result = await service.handle_response(
        user_id=user_id,
        profile=profile,
        step="SELECT_PREFERENCE",
        response="briefing",
    )

    assert result.step == "EDIT_BRIEFING_ENABLED"

    assert "Enabled" in result.message


@pytest.mark.asyncio
async def test_briefing_time_alias_resolves_correctly(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="SELECT_PREFERENCE",
        response="briefing time",
    )

    assert result.step == "EDIT_BRIEFING_TIME"

    assert "08:00" in result.message


@pytest.mark.asyncio
async def test_interests_alias_resolves_correctly(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="SELECT_PREFERENCE",
        response="interests",
    )

    assert result.step == "EDIT_INTERESTS"

    assert "AI" in result.message
    assert "technology" in result.message


@pytest.mark.asyncio
async def test_watchlist_alias_resolves_to_tracked_entities(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="SELECT_PREFERENCE",
        response="watchlist",
    )

    assert result.step == "EDIT_TRACKED_ENTITIES"

    assert "NVIDIA" in result.message


@pytest.mark.asyncio
async def test_invalid_preference_selection_is_rejected(
    service,
    profile,
    profile_repository,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="SELECT_PREFERENCE",
        response="something completely unknown",
    )

    profile_repository.create_or_update_profile.assert_not_awaited()

    assert result.step == "SELECT_PREFERENCE"
    assert result.completed is False

    assert "change" in result.message.lower()


# ============================================================
# EDIT INTERESTS
# ============================================================


@pytest.mark.asyncio
async def test_edit_interests_accepts_custom_values(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_INTERESTS",
        response="Semiconductors, renewable energy",
    )

    assert result.step == "CONFIRM_CHANGE"

    assert "Semiconductors" in result.message
    assert "renewable energy" in result.message
    assert "save" in result.message.lower()


@pytest.mark.asyncio
async def test_edit_interests_removes_duplicate_values(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_INTERESTS",
        response="AI, AI, startups, ai",
    )

    assert result.step == "CONFIRM_CHANGE"

    assert "AI" in result.message
    assert "startups" in result.message


# ============================================================
# EDIT WATCHLIST
# ============================================================


@pytest.mark.asyncio
async def test_edit_watchlist_accepts_custom_company(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_TRACKED_ENTITIES",
        response="AMD, Tata Motors",
    )

    assert result.step == "CONFIRM_CHANGE"

    assert "AMD" in result.message
    assert "Tata Motors" in result.message


# ============================================================
# EDIT BRIEFING
# ============================================================



@pytest.mark.asyncio
async def test_enable_briefing(
    service,
    profile,
):
    profile.briefing_enabled = False

    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_BRIEFING_ENABLED",
        response="yes",
    )

    assert result.step == "CONFIRM_CHANGE"
    assert "Enabled" in result.message
    assert "Disabled" in result.message


@pytest.mark.asyncio
async def test_disable_briefing(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_BRIEFING_ENABLED",
        response="no",
    )

    assert result.step == "CONFIRM_CHANGE"
    assert "Enabled" in result.message
    assert "Disabled" in result.message




@pytest.mark.asyncio
async def test_invalid_briefing_value_is_rejected(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_BRIEFING_ENABLED",
        response="maybe",
    )

    assert result.step == "EDIT_BRIEFING_ENABLED"
    assert result.completed is False


# ============================================================
# EDIT BRIEFING TIME
# ============================================================


@pytest.mark.asyncio
async def test_briefing_time_is_parsed(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_BRIEFING_TIME",
        response="9:30 PM",
    )

    assert result.step == "CONFIRM_CHANGE"

    assert "21:30" in result.message


@pytest.mark.asyncio
async def test_invalid_briefing_time_is_rejected(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_BRIEFING_TIME",
        response="whenever",
    )

    assert result.step == "EDIT_BRIEFING_TIME"
    assert result.completed is False


# ============================================================
# EDIT TIMEZONE
# ============================================================


@pytest.mark.asyncio
async def test_timezone_can_be_changed(
    service,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_TIMEZONE",
        response="America/New_York",
    )

    assert result.step == "CONFIRM_CHANGE"

    assert "America/New_York" in result.message


# ============================================================
# CONFIRMATION SAFETY
# ============================================================


@pytest.mark.asyncio
async def test_preference_is_not_updated_before_confirmation(
    service,
    profile_repository,
    profile,
):
    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="EDIT_INTERESTS",
        response="finance, markets",
    )

    assert result.step == "CONFIRM_CHANGE"

    profile_repository.create_or_update_profile.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirmation_yes_updates_database(
    service,
    profile_repository,
    profile,
):
    user_id = uuid4()

    change = PreferenceChange(
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

    result = await service.handle_response(
        user_id=user_id,
        profile=profile,
        step="CONFIRM_CHANGE",
        response="yes",
        pending_change=change,
    )

    profile_repository.create_or_update_profile.assert_awaited_once_with(
        user_id=user_id,
        interests=[
            "finance",
            "markets",
        ],
    )

    assert result.step == "UPDATED"
    assert result.completed is True


@pytest.mark.asyncio
async def test_confirmation_no_does_not_update_database(
    service,
    profile_repository,
    profile,
):
    change = PreferenceChange(
        field="interests",
        old_value=["AI"],
        new_value=["finance"],
    )

    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="CONFIRM_CHANGE",
        response="no",
        pending_change=change,
    )

    profile_repository.create_or_update_profile.assert_not_awaited()

    assert result.step == "SELECT_PREFERENCE"
    assert result.completed is False


@pytest.mark.asyncio
async def test_invalid_confirmation_is_rejected(
    service,
    profile_repository,
    profile,
):
    change = PreferenceChange(
        field="interests",
        old_value=["AI"],
        new_value=["finance"],
    )

    result = await service.handle_response(
        user_id=uuid4(),
        profile=profile,
        step="CONFIRM_CHANGE",
        response="maybe",
        pending_change=change,
    )

    profile_repository.create_or_update_profile.assert_not_awaited()

    assert result.step == "CONFIRM_CHANGE"
    assert result.completed is False


# ============================================================
# PENDING CHANGE SAFETY
# ============================================================


@pytest.mark.asyncio
async def test_confirmation_without_pending_change_raises_error(
    service,
    profile,
):
    with pytest.raises(ValueError):
        await service.handle_response(
            user_id=uuid4(),
            profile=profile,
            step="CONFIRM_CHANGE",
            response="yes",
            pending_change=None,
        )


# ============================================================
# WARM UX
# ============================================================


def test_preference_summary_is_user_friendly(
    service,
    profile,
):
    message = service._preference_summary(
        profile
    )

    assert "Of course" in message
    assert "Role" in message
    assert "Interests" in message
    assert "Watchlist" in message
    assert "Daily briefing" in message


def test_confirmation_message_is_clear(
    service,
):
    change = PreferenceChange(
        field="briefing_time",
        old_value="08:00",
        new_value="21:30",
    )

    message = service._confirmation_message(
        change
    )

    assert "Current" in message
    assert "New" in message
    assert "08:00" in message
    assert "21:30" in message
    assert "save" in message.lower()

