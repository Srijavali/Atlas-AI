from typing import Any

from telegram import Bot


class TelegramMediaFetcher:
    """
    Downloads Telegram media using a Telegram file_id.

    Telegram-specific file retrieval remains isolated here.
    """

    def __init__(
        self,
        bot: Bot,
    ) -> None:
        self._bot = bot

    async def fetch(
        self,
        file_id: str,
    ) -> bytes:
        if not isinstance(file_id, str):
            raise TypeError(
                "Telegram media file_id must be a string"
            )

        file_id = file_id.strip()

        if not file_id:
            raise ValueError(
                "Telegram media file_id cannot be empty"
            )

        telegram_file = await self._bot.get_file(
            file_id
        )

        data = await telegram_file.download_as_bytearray()

        return bytes(data)