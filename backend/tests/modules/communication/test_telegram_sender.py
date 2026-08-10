from unittest.mock import AsyncMock

import pytest

from backend.modules.communication.telegram.sender import TelegramSender


@pytest.mark.asyncio
async def test_send_text():
    bot = AsyncMock()
    bot.send_message.return_value = "sent"

    sender = TelegramSender(bot)

    result = await sender.send_text(
        chat_id=123456,
        text="Hello Sri",
    )

    bot.send_message.assert_awaited_once_with(
        chat_id=123456,
        text="Hello Sri",
    )

    assert result == "sent"


@pytest.mark.asyncio
async def test_send_keyboard():
    bot = AsyncMock()
    bot.send_message.return_value = "sent"

    keyboard = object()

    sender = TelegramSender(bot)

    result = await sender.send_keyboard(
        chat_id=123456,
        text="Choose an option",
        keyboard=keyboard,
    )

    bot.send_message.assert_awaited_once_with(
        chat_id=123456,
        text="Choose an option",
        reply_markup=keyboard,
    )

    assert result == "sent"


@pytest.mark.asyncio
async def test_answer_callback():
    bot = AsyncMock()
    bot.answer_callback_query.return_value = True

    sender = TelegramSender(bot)

    result = await sender.answer_callback(
        callback_query_id="callback-123",
        text="Saved!",
    )

    bot.answer_callback_query.assert_awaited_once_with(
        callback_query_id="callback-123",
        text="Saved!",
    )

    assert result is True


@pytest.mark.asyncio
async def test_answer_callback_without_text():
    bot = AsyncMock()

    sender = TelegramSender(bot)

    await sender.answer_callback(
        callback_query_id="callback-123",
    )

    bot.answer_callback_query.assert_awaited_once_with(
        callback_query_id="callback-123",
        text=None,
    )