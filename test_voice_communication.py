import asyncio
from uuid import uuid4

from backend.domain.enums import InteractionType, Platform
from backend.domain.models.interaction import IncomingInteraction
from backend.persistence.models.user import OnboardingStatus
from backend.modules.communication.service import CommunicationService


class FakeUser:
    id = 1
    onboarding_status = OnboardingStatus.COMPLETED


class FakeUserRepository:
    async def get_by_telegram_user_id(self, telegram_user_id):
        return FakeUser()

    async def update_last_seen(self, user_id):
        pass


class FakeOnboardingRepository:
    async def get_by_user_id(self, user_id):
        return None


class FakeOnboardingService:
    async def start(self, user_id):
        raise AssertionError(
            "Onboarding should not run for this test"
        )

    async def handle_response(self, session, response):
        raise AssertionError(
            "Onboarding should not run for this test"
        )


class FakeMediaFetcher:
    async def fetch(self, media_reference):
        print(
            f"[FAKE MEDIA] Fetching: {media_reference}"
        )

        return b"fake audio bytes"


class FakeSpeechToText:
    async def transcribe(
        self,
        *,
        audio,
        filename,
    ):
        print(
            f"[FAKE STT] Transcribing: {filename}"
        )

        return "What is the revenue of NVIDIA?"


class FakeAtlasAgent:
    async def respond(
        self,
        *,
        text,
        user_context=None,
    ):
        print(
            f"[FAKE ATLAS] Received: {text}"
        )

        return (
            "NVIDIA reported revenue of "
            "$81.6 billion."
        )


class FakePreprocessingService:
    def process_text(self, text):
        raise AssertionError(
            "Text preprocessing should not run"
        )

    def process_document(self, content, *, filename):
        raise AssertionError(
            "Document preprocessing should not run"
        )

    def process_audio(self, content, *, filename):
        raise AssertionError(
            "Legacy audio preprocessing should not run"
        )


async def main():
    service = CommunicationService(
        user_repository=FakeUserRepository(),
        onboarding_repository=FakeOnboardingRepository(),
        onboarding_service=FakeOnboardingService(),
        preprocessing_service=FakePreprocessingService(),
        media_fetcher=FakeMediaFetcher(),
        speech_to_text=FakeSpeechToText(),
        atlas_agent=FakeAtlasAgent(),
    )

    interaction = IncomingInteraction(
    interaction_id=str(uuid4()),
    platform=Platform.TELEGRAM,
    platform_event_id="test-event-voice-001",
    user_id="123456",
    conversation_id="123456",
    interaction_type=InteractionType.VOICE,
    media_reference="test-voice-file",
    metadata={
        "filename": "voice.ogg",
    },
)

    response = await service.handle(
        interaction
    )

    print("\nVoice communication response:")
    print(response)

    assert response == (
        "NVIDIA reported revenue of "
        "$81.6 billion."
    )

    print("\nVoice communication test passed.")


if __name__ == "__main__":
    asyncio.run(main())