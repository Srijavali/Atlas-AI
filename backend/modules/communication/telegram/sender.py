from typing import Any

from telegram import Bot, InlineKeyboardMarkup


class TelegramSender:
    """Send outbound messages through the Telegram Bot API."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_text(
        self,
        chat_id: int | str,
        text: str,
    ) -> Any:
        return await self.bot.send_message(
            chat_id=chat_id,
            text=text,
        )

    async def send_keyboard(
        self,
        chat_id: int | str,
        text: str,
        keyboard: InlineKeyboardMarkup,
    ) -> Any:
        return await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
        )

    async def answer_callback(
        self,
        callback_query_id: str,
        text: str | None = None,
    ) -> Any:
        return await self.bot.answer_callback_query(
            callback_query_id=callback_query_id,
            text=text,
        )