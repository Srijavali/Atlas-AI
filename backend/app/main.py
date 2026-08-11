from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram import Bot

from backend.api.router import api_router
from backend.configuration.settings import settings

from backend.modules.background.service import BackgroundService
from backend.modules.background.worker import BackgroundWorker

from backend.modules.brain.service import AtlasAgent

from backend.modules.communication.telegram.sender import (
    TelegramSender,
)

from backend.modules.notifications.service import (
    NotificationService,
)

from backend.modules.scheduler.service import (
    SchedulerService,
)

from backend.infrastructure.llm import GroqRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start and stop Atlas infrastructure
    with the FastAPI application lifecycle.
    """

    # =========================================================
    # VALIDATION
    # =========================================================

    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured"
        )

    if not settings.WEBHOOK_URL:
        raise RuntimeError(
            "WEBHOOK_URL is not configured"
        )

    # =========================================================
    # CORE ATLAS DEPENDENCIES
    # =========================================================

    groq_router = GroqRouter()

    atlas_agent = AtlasAgent(
        llm=groq_router,
    )

    # =========================================================
    # TELEGRAM BOT
    # =========================================================

    telegram_bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
    )

    # Initialize ONE Telegram Bot instance.
    await telegram_bot.initialize()

    # ---------------------------------------------------------
    # Register Telegram webhook
    # ---------------------------------------------------------

    webhook_kwargs = {
        "url": settings.WEBHOOK_URL,
    }

    if settings.WEBHOOK_SECRET:
        webhook_kwargs["secret_token"] = (
            settings.WEBHOOK_SECRET
        )

    await telegram_bot.set_webhook(
        **webhook_kwargs
    )

    telegram_sender = TelegramSender(
        telegram_bot,
    )

    # =========================================================
    # ASYNC SUBSYSTEM
    # =========================================================

    notification_service = NotificationService(
        telegram_sender=telegram_sender,
    )

    background_worker = BackgroundWorker(
        max_concurrency=2,
    )

    background_service = BackgroundService(
        worker=background_worker,
    )

    scheduler_service = SchedulerService(
        worker=background_worker,
        atlas_agent=atlas_agent,
        notification_service=notification_service,
    )

    # =========================================================
    # APPLICATION STATE
    # =========================================================

    app.state.telegram_bot = telegram_bot
    app.state.telegram_sender = telegram_sender

    app.state.background_service = (
        background_service
    )

    app.state.scheduler_service = (
        scheduler_service
    )

    app.state.atlas_agent = atlas_agent

    # =========================================================
    # START ASYNC INFRASTRUCTURE
    # =========================================================

    await background_service.start()
    await scheduler_service.start()

    try:
        yield

    finally:

        # =====================================================
        # SHUTDOWN
        # =====================================================

        try:
            await scheduler_service.stop()
        except Exception:
            pass

        try:
            await background_service.stop()
        except Exception:
            pass

        # -----------------------------------------------------
        # IMPORTANT:
        # Do NOT delete the Telegram webhook here.
        #
        # Render may restart the service. Keeping the webhook
        # registered allows Telegram to continue delivering
        # updates after restart.
        # -----------------------------------------------------

        try:
            await telegram_bot.shutdown()
        except Exception:
            pass


app = FastAPI(
    title="Atlas AI",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "atlas-ai",
        "scheduler": "running",
        "background_worker": "running",
        "telegram": "configured",
    }