from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, Mock

import pytest

from backend.domain.enums import InteractionType, Platform
from backend.domain.models.interaction import IncomingInteraction
from backend.modules.communication.service import CommunicationService
from backend.persistence.models.user import OnboardingStatus


@pytest.fixture
def repositories():
    return {
        "user": AsyncMock(),
        "onboarding": AsyncMock(),
    }


@pytest.fixture
def onboarding_service():
    return AsyncMock()


@pytest.fixture
def preprocessing_service():
    return Mock()


@pytest.fixture
def service(
    repositories,
    onboarding_service,
    preprocessing_service,
):
    return CommunicationService(
        user_repository=repositories["user"],
        onboarding_repository=repositories["onboarding"],
        onboarding_service=onboarding_service,
        preprocessing_service=preprocessing_service,
    )


def interaction(
    *,
    user_id="123456",
    interaction_type=InteractionType.TEXT,
    text="Hello Atlas",
):
    return IncomingInteraction(
        interaction_id=str(uuid4()),
        platform=Platform.TELEGRAM,
        platform_event_id="1001",
        user_id=user_id,
        conversation_id=user_id,
        interaction_type=interaction_type,
        text=text,
        metadata={
            "telegram_user_id": int(user_id),
            "username": "sri",
            "first_name": "Sri",
        },
    )


@pytest.mark.asyncio
async def test_new_user_starts_onboarding(
    service,
    repositories,
    onboarding_service,
):
    user = SimpleNamespace(
        id=uuid4(),
        onboarding_status=OnboardingStatus.NOT_STARTED,
    )

    repositories["user"].get_by_telegram_user_id.return_value = None
    repositories["user"].create_user.return_value = user

    onboarding_service.start.return_value = SimpleNamespace(
        message="Hey! 👋 I'm Atlas.",
        completed=False,
    )

    result = await service.handle(
        interaction(
            interaction_type=InteractionType.COMMAND,
            text="/start",
        )
    )

    assert result == "Hey! 👋 I'm Atlas."

    repositories["user"].create_user.assert_awaited_once_with(
        telegram_user_id=123456,
        telegram_username="sri",
        display_name="Sri",
    )

    onboarding_service.start.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_existing_incomplete_user_resumes_onboarding(
    service,
    repositories,
    onboarding_service,
):
    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        onboarding_status=OnboardingStatus.IN_PROGRESS,
    )

    session = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        current_step="ASK_NAME",
    )

    repositories["user"].get_by_telegram_user_id.return_value = user
    repositories["onboarding"].get_by_user_id.return_value = session

    onboarding_service.handle_response.return_value = SimpleNamespace(
        message="Nice to meet you! 😊",
        completed=False,
    )

    result = await service.handle(
        interaction(text="Sri")
    )

    assert result == "Nice to meet you! 😊"

    onboarding_service.handle_response.assert_awaited_once_with(
        session=session,
        response="Sri",
    )


@pytest.mark.asyncio
async def test_completed_user_goes_to_preprocessor(
    service,
    repositories,
    preprocessing_service,
):
    user = SimpleNamespace(
        id=uuid4(),
        onboarding_status=OnboardingStatus.COMPLETED,
    )

    repositories["user"].get_by_telegram_user_id.return_value = user

    preprocessing_service.process_text.return_value = SimpleNamespace(
        text="hello atlas",
    )

    result = await service.handle(
        interaction(text="  Hello Atlas  ")
    )

    assert result == "hello atlas"

    preprocessing_service.process_text.assert_called_once_with(
        "  Hello Atlas  "
    )


@pytest.mark.asyncio
async def test_completed_user_start_does_not_restart_onboarding(
    service,
    repositories,
    onboarding_service,
):
    user = SimpleNamespace(
        id=uuid4(),
        onboarding_status=OnboardingStatus.COMPLETED,
    )

    repositories["user"].get_by_telegram_user_id.return_value = user

    result = await service.handle(
        interaction(
            interaction_type=InteractionType.COMMAND,
            text="/start",
        )
    )

    assert "already set up" in result

    onboarding_service.start.assert_not_awaited()