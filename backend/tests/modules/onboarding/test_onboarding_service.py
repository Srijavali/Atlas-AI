from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from backend.modules.onboarding.service import OnboardingService
from backend.persistence.models.onboarding import SessionStatus
from backend.persistence.models.user import OnboardingStatus


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def onboarding_repository():
    repository = Mock()

    repository.get_by_user_id = AsyncMock()
    repository.create_session = AsyncMock()
    repository.update_step_data = AsyncMock()
    repository.complete_session = AsyncMock()

    return repository


@pytest.fixture
def user_repository():
    repository = Mock()

    repository.update_onboarding_status = AsyncMock()

    return repository


@pytest.fixture
def profile_repository():
    repository = Mock()

    repository.create_or_update_profile = AsyncMock()

    return repository


@pytest.fixture
def service(
    onboarding_repository,
    user_repository,
    profile_repository,
):
    return OnboardingService(
        onboarding_repository=onboarding_repository,
        user_repository=user_repository,
        profile_repository=profile_repository,
    )


def make_session(
    *,
    current_step: str,
    temporary_data: dict | None = None,
):
    session = Mock()

    session.id = uuid4()
    session.user_id = uuid4()
    session.current_step = current_step
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = temporary_data or {}

    return session


# ============================================================
# START / RESUME
# ============================================================


@pytest.mark.asyncio
async def test_new_user_starts_onboarding(
    service,
    onboarding_repository,
):
    user_id = uuid4()

    onboarding_repository.get_by_user_id.return_value = None

    result = await service.start(user_id)

    onboarding_repository.create_session.assert_awaited_once_with(
        user_id=user_id,
        initial_step="WELCOME",
    )

    assert result.step == "WELCOME"
    assert result.completed is False
    assert "Atlas" in result.message


@pytest.mark.asyncio
async def test_existing_onboarding_session_is_resumed(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_INTERESTS",
        temporary_data={
            "display_name": "Sri",
        },
    )

    onboarding_repository.get_by_user_id.return_value = session

    result = await service.start(session.user_id)

    onboarding_repository.create_session.assert_not_awaited()

    assert result.step == "ASK_INTERESTS"
    assert result.completed is False
    assert result.message


@pytest.mark.asyncio
async def test_completed_onboarding_is_reported_as_completed(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="COMPLETED",
    )

    session.status = SessionStatus.COMPLETED

    onboarding_repository.get_by_user_id.return_value = session

    result = await service.start(session.user_id)

    assert result.step == "COMPLETED"
    assert result.completed is True


# ============================================================
# WELCOME -> NAME
# ============================================================


@pytest.mark.asyncio
async def test_welcome_moves_to_name_step(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="WELCOME",
    )

    result = await service.handle_response(
        session=session,
        response="Hi",
    )

    onboarding_repository.update_step_data.assert_awaited_once()

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_NAME"

    assert result.step == "ASK_NAME"
    assert result.completed is False


# ============================================================
# NAME -> INTERESTS
# ============================================================


@pytest.mark.asyncio
async def test_name_is_saved_and_interests_are_requested(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_NAME",
    )

    result = await service.handle_response(
        session=session,
        response="Sri",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_INTERESTS"

    assert (
        call.kwargs["temporary_data"]["display_name"]
        == "Sri"
    )

    assert result.step == "ASK_INTERESTS"


@pytest.mark.asyncio
async def test_empty_name_is_rejected(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_NAME",
    )

    result = await service.handle_response(
        session=session,
        response="   ",
    )

    onboarding_repository.update_step_data.assert_not_awaited()

    assert result.step == "ASK_NAME"
    assert result.completed is False
    assert "name" in result.message.lower()


# ============================================================
# INTERESTS
# ============================================================


@pytest.mark.asyncio
async def test_interests_are_saved_and_watchlist_is_requested(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_INTERESTS",
        temporary_data={
            "display_name": "Sri",
        },
    )

    result = await service.handle_response(
        session=session,
        response="AI, technology, startups",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_WATCHLIST"

    assert call.kwargs["temporary_data"]["interests"] == [
        "AI",
        "technology",
        "startups",
    ]

    assert result.step == "ASK_WATCHLIST"


@pytest.mark.asyncio
async def test_interests_support_custom_free_text(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_INTERESTS",
    )

    result = await service.handle_response(
        session=session,
        response="Semiconductors, renewable energy",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["temporary_data"]["interests"] == [
        "Semiconductors",
        "renewable energy",
    ]

    assert result.step == "ASK_WATCHLIST"


@pytest.mark.asyncio
async def test_interests_can_be_skipped(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_INTERESTS",
    )

    result = await service.handle_response(
        session=session,
        response="skip",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_WATCHLIST"

    assert call.kwargs["temporary_data"]["interests"] == []

    assert result.step == "ASK_WATCHLIST"


# ============================================================
# WATCHLIST
# ============================================================


@pytest.mark.asyncio
async def test_watchlist_is_saved_and_daily_briefing_is_requested(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_WATCHLIST",
    )

    result = await service.handle_response(
        session=session,
        response="NVIDIA, Microsoft, semiconductors",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_DAILY_BRIEFING"

    assert call.kwargs["temporary_data"][
        "tracked_entities"
    ] == [
        "NVIDIA",
        "Microsoft",
        "semiconductors",
    ]

    assert result.step == "ASK_DAILY_BRIEFING"


@pytest.mark.asyncio
async def test_watchlist_can_be_skipped(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_WATCHLIST",
    )

    result = await service.handle_response(
        session=session,
        response="skip",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["temporary_data"][
        "tracked_entities"
    ] == []

    assert result.step == "ASK_DAILY_BRIEFING"


@pytest.mark.asyncio
async def test_custom_watchlist_input_is_supported(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_WATCHLIST",
    )

    result = await service.handle_response(
        session=session,
        response="Tata Motors, AMD, semiconductor companies",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["temporary_data"][
        "tracked_entities"
    ] == [
        "Tata Motors",
        "AMD",
        "semiconductor companies",
    ]

    assert result.step == "ASK_DAILY_BRIEFING"


# ============================================================
# DAILY BRIEFING
# ============================================================


@pytest.mark.asyncio
async def test_daily_briefing_yes_requests_briefing_time(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_DAILY_BRIEFING",
    )

    result = await service.handle_response(
        session=session,
        response="yes",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_BRIEFING_TIME"

    assert (
        call.kwargs["temporary_data"]["briefing_enabled"]
        is True
    )

    assert result.step == "ASK_BRIEFING_TIME"


@pytest.mark.asyncio
async def test_daily_briefing_no_skips_to_timezone(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_DAILY_BRIEFING",
    )

    result = await service.handle_response(
        session=session,
        response="no",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_TIMEZONE"

    assert (
        call.kwargs["temporary_data"]["briefing_enabled"]
        is False
    )

    assert (
        call.kwargs["temporary_data"]["briefing_time"]
        is None
    )

    assert result.step == "ASK_TIMEZONE"


@pytest.mark.asyncio
async def test_invalid_daily_briefing_answer_is_rejected(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_DAILY_BRIEFING",
    )

    result = await service.handle_response(
        session=session,
        response="maybe",
    )

    onboarding_repository.update_step_data.assert_not_awaited()

    assert result.step == "ASK_DAILY_BRIEFING"
    assert result.completed is False


# ============================================================
# BRIEFING TIME
# ============================================================


@pytest.mark.asyncio
async def test_briefing_time_is_parsed(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_BRIEFING_TIME",
        temporary_data={
            "briefing_enabled": True,
        },
    )

    result = await service.handle_response(
        session=session,
        response="8:30 PM",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_TIMEZONE"

    assert (
        call.kwargs["temporary_data"]["briefing_time"]
        == "20:30:00"
    )

    assert result.step == "ASK_TIMEZONE"


@pytest.mark.asyncio
async def test_invalid_briefing_time_is_rejected(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_BRIEFING_TIME",
        temporary_data={
            "briefing_enabled": True,
        },
    )

    result = await service.handle_response(
        session=session,
        response="sometime later",
    )

    onboarding_repository.update_step_data.assert_not_awaited()

    assert result.step == "ASK_BRIEFING_TIME"
    assert result.completed is False


# ============================================================
# TIMEZONE
# ============================================================


@pytest.mark.asyncio
async def test_timezone_is_validated_and_confirmation_is_requested(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_TIMEZONE",
        temporary_data={
            "display_name": "Sri",
            "briefing_enabled": True,
            "briefing_time": "20:30:00",
        },
    )

    result = await service.handle_response(
        session=session,
        response="Asia/Kolkata",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "CONFIRM"

    assert (
        call.kwargs["temporary_data"]["timezone"]
        == "Asia/Kolkata"
    )

    assert result.step == "CONFIRM"

    assert "Sri" in result.message
    assert "Asia/Kolkata" in result.message


@pytest.mark.asyncio
async def test_invalid_timezone_is_rejected(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_TIMEZONE",
    )

    result = await service.handle_response(
        session=session,
        response="Not/ARealTimezone",
    )

    onboarding_repository.update_step_data.assert_not_awaited()

    assert result.step == "ASK_TIMEZONE"
    assert result.completed is False


# ============================================================
# LEGACY STEP REDIRECTS
# ============================================================


@pytest.mark.asyncio
async def test_legacy_role_step_redirects_to_interests(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_ROLE",
        temporary_data={
            "display_name": "Sri",
        },
    )

    result = await service.handle_response(
        session=session,
        response="Analyst",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_INTERESTS"

    assert result.step == "ASK_INTERESTS"


@pytest.mark.asyncio
async def test_legacy_market_preferences_redirect_to_watchlist(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_MARKET_PREFERENCES",
        temporary_data={
            "display_name": "Sri",
            "interests": ["AI"],
        },
    )

    result = await service.handle_response(
        session=session,
        response="Stocks, ETFs",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_WATCHLIST"

    assert result.step == "ASK_WATCHLIST"


@pytest.mark.asyncio
async def test_legacy_insight_preferences_redirect_to_daily_briefing(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_INSIGHT_PREFERENCES",
        temporary_data={
            "display_name": "Sri",
            "tracked_entities": ["NVIDIA"],
        },
    )

    result = await service.handle_response(
        session=session,
        response="Earnings, filings",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_DAILY_BRIEFING"

    assert result.step == "ASK_DAILY_BRIEFING"


@pytest.mark.asyncio
async def test_legacy_alerts_redirect_to_daily_briefing(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_ALERTS",
        temporary_data={
            "display_name": "Sri",
            "tracked_entities": ["NVIDIA"],
        },
    )

    result = await service.handle_response(
        session=session,
        response="Company news",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_DAILY_BRIEFING"

    assert result.step == "ASK_DAILY_BRIEFING"


# ============================================================
# CONFIRMATION
# ============================================================


@pytest.mark.asyncio
async def test_confirmation_yes_completes_onboarding(
    service,
    onboarding_repository,
    user_repository,
    profile_repository,
):
    session = make_session(
        current_step="CONFIRM",
        temporary_data={
            "display_name": "Sri",
            "interests": [
                "AI",
                "technology",
            ],
            "tracked_entities": [
                "NVIDIA",
                "Microsoft",
            ],
            "briefing_enabled": True,
            "briefing_time": "20:30:00",
            "timezone": "Asia/Kolkata",
        },
    )

    result = await service.handle_response(
        session=session,
        response="yes",
    )

    onboarding_repository.complete_session.assert_awaited_once_with(
        session.id
    )

    user_repository.update_onboarding_status.assert_awaited_once_with(
        user_id=session.user_id,
        status=OnboardingStatus.COMPLETED,
        display_name="Sri",
    )

    profile_repository.create_or_update_profile.assert_awaited_once_with(
        user_id=session.user_id,
        role=None,
        interests=[
            "AI",
            "technology",
        ],
        market_preferences=[],
        tracked_entities=[
            "NVIDIA",
            "Microsoft",
        ],
        insight_preferences=[],
        alert_preferences=[],
        briefing_enabled=True,
        briefing_time=service._parse_stored_time(
            "20:30:00"
        ),
        timezone_str="Asia/Kolkata",
    )

    assert result.step == "COMPLETED"
    assert result.completed is True
    assert "Atlas" in result.message


@pytest.mark.asyncio
async def test_confirmation_change_does_not_complete_onboarding(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="CONFIRM",
    )

    result = await service.handle_response(
        session=session,
        response="change",
    )

    onboarding_repository.complete_session.assert_not_awaited()

    assert result.step == "CONFIRM"
    assert result.completed is False
    assert "change" in result.message.lower()


def test_confirmation_message_shows_user_preferences(
    service,
):
    session = make_session(
        current_step="CONFIRM",
        temporary_data={
            "display_name": "Sri",
            "interests": [
                "AI",
                "technology",
            ],
            "tracked_entities": [
                "NVIDIA",
                "Microsoft",
            ],
            "briefing_enabled": True,
            "briefing_time": "20:30:00",
            "timezone": "Asia/Kolkata",
        },
    )

    message = service._message_for_step(
        "CONFIRM",
        session=session,
    )

    assert "Sri" in message
    assert "AI" in message
    assert "technology" in message
    assert "NVIDIA" in message
    assert "Microsoft" in message
    assert "Asia/Kolkata" in message
    assert "yes" in message.lower()


# ============================================================
# HYBRID / CUSTOM INPUT
# ============================================================


@pytest.mark.asyncio
async def test_duplicate_custom_values_are_removed(
    service,
    onboarding_repository,
):
    session = make_session(
        current_step="ASK_INTERESTS",
    )

    result = await service.handle_response(
        session=session,
        response="AI, AI, startups, ai",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["temporary_data"]["interests"] == [
        "AI",
        "startups",
    ]

    assert result.step == "ASK_WATCHLIST"


# ============================================================
# COMPLETION MESSAGE
# ============================================================


def test_completion_message_is_warm(
    service,
):
    message = service._message_for_step(
        "COMPLETED"
    )

    assert "all set" in message.lower()
    assert "Atlas" in message
    assert "ready" in message.lower()