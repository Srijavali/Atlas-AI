
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from backend.persistence.models.onboarding import SessionStatus
from backend.persistence.models.user import OnboardingStatus
from backend.modules.onboarding.service import OnboardingService


@pytest.fixture
def onboarding_repository():
    return Mock()


@pytest.fixture
def user_repository():
    return Mock()


@pytest.fixture
def profile_repository():
    return Mock()


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


@pytest.mark.asyncio
async def test_new_user_starts_onboarding(
    service,
    onboarding_repository,
):
    user_id = uuid4()

    onboarding_repository.get_by_user_id = AsyncMock(
        return_value=None
    )
    onboarding_repository.create_session = AsyncMock()

    result = await service.start(user_id)

    onboarding_repository.create_session.assert_awaited_once_with(
        user_id=user_id,
        initial_step="WELCOME",
    )

    assert result.step == "WELCOME"
    assert result.message


@pytest.mark.asyncio
async def test_existing_onboarding_session_is_resumed(
    service,
    onboarding_repository,
):
    user_id = uuid4()

    session = Mock()
    session.current_step = "ASK_NAME"
    session.status = SessionStatus.IN_PROGRESS

    onboarding_repository.get_by_user_id = AsyncMock(
        return_value=session
    )

    result = await service.start(user_id)

    onboarding_repository.create_session.assert_not_called()

    assert result.step == "ASK_NAME"
    assert result.message


@pytest.mark.asyncio
async def test_welcome_moves_to_name_step(
    service,
    onboarding_repository,
):
    session = Mock()
    session.id = uuid4()
    session.current_step = "WELCOME"
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = {}

    onboarding_repository.update_step_data = AsyncMock(
        return_value=session
    )

    result = await service.handle_response(
        session=session,
        response="Hi",
    )

    onboarding_repository.update_step_data.assert_awaited_once()

    assert result.step == "ASK_NAME"
    assert result.message


@pytest.mark.asyncio
async def test_name_is_saved_and_timezone_is_requested(
    service,
    onboarding_repository,
):
    session = Mock()
    session.id = uuid4()
    session.current_step = "ASK_NAME"
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = {}

    onboarding_repository.update_step_data = AsyncMock(
        return_value=session
    )

    result = await service.handle_response(
        session=session,
        response="Sri",
    )

    onboarding_repository.update_step_data.assert_awaited_once()

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_TIMEZONE"
    assert call.kwargs["temporary_data"]["display_name"] == "Sri"

    assert result.step == "ASK_TIMEZONE"


@pytest.mark.asyncio
async def test_empty_name_is_rejected(
    service,
    onboarding_repository,
):
    session = Mock()
    session.id = uuid4()
    session.current_step = "ASK_NAME"
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = {}

    result = await service.handle_response(
        session=session,
        response="   ",
    )

    onboarding_repository.update_step_data.assert_not_called()

    assert result.step == "ASK_NAME"
    assert "name" in result.message.lower()


@pytest.mark.asyncio
async def test_timezone_is_saved_and_interests_are_requested(
    service,
    onboarding_repository,
):
    session = Mock()
    session.id = uuid4()
    session.current_step = "ASK_TIMEZONE"
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = {
        "display_name": "Sri",
    }

    onboarding_repository.update_step_data = AsyncMock(
        return_value=session
    )

    result = await service.handle_response(
        session=session,
        response="Asia/Kolkata",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_INTERESTS"
    assert call.kwargs["temporary_data"]["timezone"] == "Asia/Kolkata"

    assert result.step == "ASK_INTERESTS"


@pytest.mark.asyncio
async def test_interests_are_saved_and_briefing_is_requested(
    service,
    onboarding_repository,
):
    session = Mock()
    session.id = uuid4()
    session.current_step = "ASK_INTERESTS"
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = {
        "display_name": "Sri",
        "timezone": "Asia/Kolkata",
    }

    onboarding_repository.update_step_data = AsyncMock(
        return_value=session
    )

    result = await service.handle_response(
        session=session,
        response="AI, technology, startups",
    )

    call = onboarding_repository.update_step_data.await_args

    assert call.kwargs["current_step"] == "ASK_BRIEFING"
    assert call.kwargs["temporary_data"]["interests"] == [
        "AI",
        "technology",
        "startups",
    ]

    assert result.step == "ASK_BRIEFING"


@pytest.mark.asyncio
async def test_briefing_preference_completes_onboarding(
    service,
    onboarding_repository,
    user_repository,
    profile_repository,
):
    session = Mock()
    session.id = uuid4()
    session.user_id = uuid4()
    session.current_step = "ASK_BRIEFING"
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = {
        "display_name": "Sri",
        "timezone": "Asia/Kolkata",
        "interests": ["AI", "technology"],
    }

    onboarding_repository.complete_session = AsyncMock(
        return_value=session
    )
    user_repository.update_onboarding_status = AsyncMock()
    profile_repository.create_or_update_profile = AsyncMock()

    result = await service.handle_response(
        session=session,
        response="yes",
    )

    onboarding_repository.complete_session.assert_awaited_once_with(
        session.id
    )

    user_repository.update_onboarding_status.assert_awaited_once()

    profile_repository.create_or_update_profile.assert_awaited_once()

    assert result.step == "COMPLETED"
    assert result.completed is True


@pytest.mark.asyncio
async def test_invalid_briefing_answer_is_rejected(
    service,
    onboarding_repository,
):
    session = Mock()
    session.id = uuid4()
    session.current_step = "ASK_BRIEFING"
    session.status = SessionStatus.IN_PROGRESS
    session.temporary_data = {}

    result = await service.handle_response(
        session=session,
        response="maybe",
    )

    onboarding_repository.complete_session.assert_not_called()

    assert result.step == "ASK_BRIEFING"
    assert result.completed is False

