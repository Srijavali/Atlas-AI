from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

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


# ============================================================
# TELEGRAM BOT
# ============================================================

def get_telegram_bot(request: Request):
    """
    Returns the single application-level Telegram Bot instance.

    The Bot is created and initialized once during FastAPI
    startup in main.py.

    We must NOT create Bot() separately for every request.
    """

    telegram_bot = getattr(
        request.app.state,
        "telegram_bot",
        None,
    )

    if telegram_bot is None:
        raise RuntimeError(
            "Telegram Bot is not initialized"
        )

    return telegram_bot


def get_telegram_sender(
    request: Request,
) -> TelegramSender:
    """
    Returns the application-level TelegramSender.

    TelegramSender uses the same long-lived Bot instance
    created during FastAPI startup.
    """

    telegram_sender = getattr(
        request.app.state,
        "telegram_sender",
        None,
    )

    if telegram_sender is None:
        raise RuntimeError(
            "TelegramSender is not initialized"
        )

    return telegram_sender


def get_telegram_media_fetcher(
    request: Request,
) -> TelegramMediaFetcher:
    """
    Returns a TelegramMediaFetcher using the same
    application-level Telegram Bot instance.
    """

    telegram_bot = get_telegram_bot(request)

    return TelegramMediaFetcher(
        telegram_bot
    )


# ============================================================
# SCHEDULER
# ============================================================

def get_scheduler_service(
    request: Request,
) -> SchedulerService:
    """
    Returns the application-level SchedulerService.
    """

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


# ============================================================
# DATABASE REPOSITORIES
# ============================================================

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


# ============================================================
# ONBOARDING
# ============================================================

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


# ============================================================
# IMAGE PROCESSING
# ============================================================

def get_image_processor() -> ImageProcessor:
    """
    Provides deterministic image validation and preparation.
    """

    return ImageProcessor()


# ============================================================
# VISION PROCESSING
# ============================================================

def get_vision_processor() -> VisionProcessor:
    """
    Provides Gemini-backed visual understanding.
    """

    return VisionProcessor(
        backend=GeminiVisionBackend()
    )


# ============================================================
# PREPROCESSING
# ============================================================

def get_preprocessing_service() -> PreprocessingService:
    """
    Provides the Atlas preprocessing service.

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
                    f"{name} processor is not enabled "
                    "in the MVP runtime"
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


# ============================================================
# GROQ ROUTER
# ============================================================

def get_groq_router() -> GroqRouter:
    """
    Provides the Atlas Groq LLM router.
    """

    return GroqRouter()


# ============================================================
# ATLAS BRAIN
# ============================================================

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


# ============================================================
# SPEECH TO TEXT
# ============================================================

def get_speech_to_text() -> GroqSpeechToText:
    """
    Provides Groq speech-to-text for Telegram
    voice messages.
    """

    return GroqSpeechToText()


# ============================================================
# TELEGRAM PARSER / ADAPTER
# ============================================================

def get_telegram_parser() -> TelegramParser:
    return TelegramParser()


def get_telegram_adapter() -> TelegramAdapter:
    return TelegramAdapter()


# ============================================================
# COMMUNICATION SERVICE
# ============================================================

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
    scheduler_service: SchedulerService = Depends(
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