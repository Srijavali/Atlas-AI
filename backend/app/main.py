from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram import Bot

from backend.api.router import api_router
from backend.configuration.settings import settings
from backend.modules.background.service import BackgroundService
from backend.modules.background.worker import BackgroundWorker
from backend.modules.brain.service import AtlasAgent
from backend.modules.communication.telegram.sender import TelegramSender
from backend.modules.notifications.service import NotificationService
from backend.modules.scheduler.service import SchedulerService
from backend.infrastructure.llm import GroqRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start and stop Atlas background infrastructure
    with the FastAPI application lifecycle.
    """

    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured"
        )

    # ---------------------------------------------------------
    # Core Atlas dependencies
    # ---------------------------------------------------------

    groq_router = GroqRouter()

    atlas_agent = AtlasAgent(
        llm=groq_router,
    )

    telegram_bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
    )

    telegram_sender = TelegramSender(
        telegram_bot,
    )

    # ---------------------------------------------------------
    # Async subsystem
    # ---------------------------------------------------------

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

    # Store services on application state.
    app.state.background_service = background_service
    app.state.scheduler_service = scheduler_service

    # ---------------------------------------------------------
    # Start async infrastructure
    # ---------------------------------------------------------

    await background_service.start()
    await scheduler_service.start()

    try:
        yield

    finally:
        # -----------------------------------------------------
        # Shutdown
        # -----------------------------------------------------

        await scheduler_service.stop()
        await background_service.stop()

        await telegram_bot.close()


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
    }