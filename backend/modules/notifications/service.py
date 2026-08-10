from __future__ import annotations

from typing import Any

from backend.modules.communication.telegram.sender import TelegramSender


class NotificationService:
    """
    Delivers already-generated Atlas notifications.

    This layer is responsible only for delivery.
    It does not perform reasoning, tool selection, or scheduling.
    """

    def __init__(
        self,
        *,
        telegram_sender: TelegramSender,
    ) -> None:
        self._telegram_sender = telegram_sender

    async def send_text(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> Any:
        if not message or not message.strip():
            raise ValueError(
                "Notification message cannot be empty"
            )

        return await self._telegram_sender.send_text(
            chat_id=telegram_user_id,
            text=message.strip(),
        )