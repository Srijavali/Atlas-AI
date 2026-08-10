
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.configuration.settings import settings
from backend.modules.communication.service import CommunicationService
from backend.modules.communication.telegram.adapter import TelegramAdapter
from backend.modules.communication.telegram.parser import TelegramParser
from backend.modules.communication.telegram.sender import TelegramSender
from backend.persistence.database import get_db_session
from backend.app.dependencies import (
    get_communication_service,
    get_telegram_adapter,
    get_telegram_parser,
    get_telegram_sender,
)


router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
)


@router.post("/webhook")
async def telegram_webhook(
    update: dict,
    session: AsyncSession = Depends(get_db_session),
    parser: TelegramParser = Depends(get_telegram_parser),
    adapter: TelegramAdapter = Depends(get_telegram_adapter),
    communication_service: CommunicationService = Depends(
        get_communication_service
    ),
    sender: TelegramSender = Depends(get_telegram_sender),
    telegram_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
):
    # Validate Telegram webhook secret when configured.
    if (
        settings.WEBHOOK_SECRET
        and telegram_secret_token != settings.WEBHOOK_SECRET
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook secret",
        )

    parsed = parser.parse(update)

    # Ignore unsupported Telegram update types.
    if parsed["update_type"] == "unsupported":
        return {
            "ok": True,
            "processed": False,
        }

    interaction = adapter.adapt(parsed)

    async with session.begin():
        response_text = await communication_service.handle(
            interaction
        )

    # Send the response after the DB transaction succeeds.
    #
    # This is intentionally enabled in development as well as
    # production so that the local ngrok -> Telegram webhook
    # demo can send responses back to the Telegram user.
    await sender.send_text(
        chat_id=interaction.conversation_id,
        text=response_text,
    )

    return {
        "ok": True,
        "processed": True,
    }

