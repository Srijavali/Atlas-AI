from backend.domain.enums import InteractionType, Platform
from backend.modules.communication.telegram.adapter import TelegramAdapter


def test_adapt_text_message():
    adapter = TelegramAdapter()

    parsed = {
        "platform_event_id": "1001",
        "telegram_user_id": 123456,
        "username": "sri",
        "first_name": "Sri",
        "chat_id": 123456,
        "message_id": 50,
        "command": None,
        "text": "Hello Atlas",
        "callback_data": None,
        "callback_query_id": None,
        "update_type": "message",
    }

    interaction = adapter.adapt(parsed)

    assert interaction.platform == Platform.TELEGRAM
    assert interaction.interaction_type == InteractionType.TEXT
    assert interaction.user_id == "123456"
    assert interaction.conversation_id == "123456"
    assert interaction.text == "Hello Atlas"
    assert interaction.platform_event_id == "1001"


def test_adapt_command():
    adapter = TelegramAdapter()

    parsed = {
        "platform_event_id": "1002",
        "telegram_user_id": 123456,
        "chat_id": 123456,
        "command": "/start",
        "text": "/start",
        "update_type": "message",
    }

    interaction = adapter.adapt(parsed)

    assert interaction.interaction_type == InteractionType.COMMAND
    assert interaction.text == "/start"


def test_adapt_callback_query():
    adapter = TelegramAdapter()

    parsed = {
        "platform_event_id": "1003",
        "telegram_user_id": 123456,
        "username": "sri",
        "first_name": "Sri",
        "chat_id": 123456,
        "message_id": 52,
        "callback_data": "market:yes",
        "callback_query_id": "callback-1",
        "command": None,
        "text": None,
        "update_type": "callback_query",
    }

    interaction = adapter.adapt(parsed)

    assert interaction.interaction_type == InteractionType.BUTTON
    assert interaction.user_id == "123456"
    assert interaction.metadata["callback_data"] == "market:yes"
    assert interaction.metadata["callback_query_id"] == "callback-1"


def test_adapter_rejects_missing_user():
    adapter = TelegramAdapter()

    parsed = {
        "chat_id": 123456,
        "update_type": "message",
    }

    try:
        adapter.adapt(parsed)
    except ValueError as exc:
        assert "user ID" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_adapter_rejects_missing_chat():
    adapter = TelegramAdapter()

    parsed = {
        "telegram_user_id": 123456,
        "update_type": "message",
    }

    try:
        adapter.adapt(parsed)
    except ValueError as exc:
        assert "chat ID" in str(exc)
    else:
        raise AssertionError("Expected ValueError")