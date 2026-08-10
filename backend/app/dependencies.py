
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot

from backend.configuration.settings import settings
from backend.persistence.database import get_db_session
from backend.persistence.repositories import (
    OnboardingRepository,
    ProfileRepository,
    UserRepository,
)

from backend.modules.onboarding.service import OnboardingService

from backend.modules.preprocessing.service import PreprocessingService
from backend.modules.preprocessing.text.normalizer import TextNormalizer
from backend.modules.preprocessing.documents.document_processor import (
    DocumentProcessor,
)
from backend.modules.preprocessing.image_processor import ImageProcessor
from backend.modules.preprocessing.vision.vision_processor import (
    VisionProcessor,
)
from backend.modules.preprocessing.vision.gemini_backend import (
    GeminiVisionBackend,
)

from backend.modules.communication.service import CommunicationService
from backend.modules.communication.telegram.adapter import TelegramAdapter
from backend.modules.communication.telegram.parser import TelegramParser
from backend.modules.communication.telegram.sender import TelegramSender
from backend.modules.communication.telegram.media import (
    TelegramMediaFetcher,
)

from backend.modules.brain.service import AtlasAgent

from backend.infrastructure.llm import GroqRouter
from backend.infrastructure.speech.groq_speech import (
    GroqSpeechToText,
)
from backend.modules.scheduler.service import SchedulerService
def get_scheduler_service(
    request: Request,
) -> SchedulerService:
    scheduler_service = getattr(
        request.app.state,
        "scheduler_service",
        None,
    )

    if scheduler_service is None:
        raise RuntimeError(
            "SchedulerService is not initialized"
        )

    return scheduler_service


def get_telegram_media_fetcher() -> TelegramMediaFetcher:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured"
        )

    return TelegramMediaFetcher(
        Bot(token=settings.TELEGRAM_BOT_TOKEN)
    )


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


def get_onboarding_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OnboardingRepository:
    return OnboardingRepository(session)


def get_profile_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProfileRepository:
    return ProfileRepository(session)


def get_onboarding_service(
    user_repository: UserRepository = Depends(
        get_user_repository
    ),
    onboarding_repository: OnboardingRepository = Depends(
        get_onboarding_repository
    ),
    profile_repository: ProfileRepository = Depends(
        get_profile_repository
    ),
) -> OnboardingService:
    return OnboardingService(
        onboarding_repository=onboarding_repository,
        user_repository=user_repository,
        profile_repository=profile_repository,
    )


def get_image_processor() -> ImageProcessor:
    """
    Provides deterministic image validation and preparation.
    """

    return ImageProcessor()


def get_vision_processor() -> VisionProcessor:
    """
    Provides Gemini-backed visual understanding.
    """

    return VisionProcessor(
        backend=GeminiVisionBackend()
    )


def get_preprocessing_service() -> PreprocessingService:
    """
    Provides the preprocessing service.

    Enabled:

        - Text normalization
        - Document processing
        - Image processing
        - Vision processing

    Disabled:

        - OCR
        - Legacy preprocessing SpeechProcessor

    Telegram voice uses the dedicated GroqSpeechToText
    integration instead of the legacy SpeechProcessor.
    """

    class DisabledProcessor:
        def __getattr__(self, name: str):
            def unavailable(*args, **kwargs):
                raise RuntimeError(
                    f"{name} processor is not enabled in the MVP runtime"
                )

            return unavailable

    return PreprocessingService(
        text_normalizer=TextNormalizer(),
        image_processor=get_image_processor(),
        ocr_processor=DisabledProcessor(),
        vision_processor=get_vision_processor(),
        document_processor=DocumentProcessor(),
        speech_processor=DisabledProcessor(),
    )


def get_groq_router() -> GroqRouter:
    """
    Provides the Atlas Groq LLM router.
    """

    return GroqRouter()


def get_atlas_agent(
    groq_router: GroqRouter = Depends(
        get_groq_router
    ),
) -> AtlasAgent:
    """
    Provides the Atlas Brain.
    """

    return AtlasAgent(
        llm=groq_router,
    )


def get_speech_to_text() -> GroqSpeechToText:
    """
    Provides Groq speech-to-text for Telegram voice messages.
    """

    return GroqSpeechToText()


def get_telegram_parser() -> TelegramParser:
    return TelegramParser()


def get_telegram_adapter() -> TelegramAdapter:
    return TelegramAdapter()


def get_telegram_sender() -> TelegramSender:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured"
        )

    return TelegramSender(
        Bot(token=settings.TELEGRAM_BOT_TOKEN)
    )


def get_communication_service(
    user_repository: UserRepository = Depends(
        get_user_repository
    ),
    onboarding_repository: OnboardingRepository = Depends(
        get_onboarding_repository
    ),
    onboarding_service: OnboardingService = Depends(
        get_onboarding_service
    ),
    preprocessing_service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
    telegram_media_fetcher: TelegramMediaFetcher = Depends(
        get_telegram_media_fetcher
    ),
    speech_to_text: GroqSpeechToText = Depends(
        get_speech_to_text
    ),
    atlas_agent: AtlasAgent = Depends(
        get_atlas_agent
    ),
    scheduler_service=Depends(
        get_scheduler_service
    ),
) -> CommunicationService:
    return CommunicationService(
        user_repository=user_repository,
        onboarding_repository=onboarding_repository,
        onboarding_service=onboarding_service,
        preprocessing_service=preprocessing_service,
        media_fetcher=telegram_media_fetcher,
        speech_to_text=speech_to_text,
        atlas_agent=atlas_agent,
        scheduler_service=scheduler_service,
    )

