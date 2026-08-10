from backend.modules.communication.telegram.parser import TelegramParser


def test_parse_text_message():
    parser = TelegramParser()

    update = {
        "update_id": 1001,
        "message": {
            "message_id": 50,
            "from": {
                "id": 123456,
                "username": "sri",
                "first_name": "Sri",
            },
            "chat": {
                "id": 123456,
            },
            "text": "Hello Atlas",
        },
    }

    result = parser.parse(update)

    assert result["platform_event_id"] == "1001"
    assert result["telegram_user_id"] == 123456
    assert result["username"] == "sri"
    assert result["first_name"] == "Sri"
    assert result["chat_id"] == 123456
    assert result["message_id"] == 50
    assert result["text"] == "Hello Atlas"
    assert result["command"] is None
    assert result["update_type"] == "message"


def test_parse_start_command():
    parser = TelegramParser()

    update = {
        "update_id": 1002,
        "message": {
            "message_id": 51,
            "from": {
                "id": 123456,
            },
            "chat": {
                "id": 123456,
            },
            "text": "/start",
        },
    }

    result = parser.parse(update)

    assert result["command"] == "/start"
    assert result["text"] == "/start"


def test_parse_callback_query():
    parser = TelegramParser()

    update = {
        "update_id": 1003,
        "callback_query": {
            "id": "callback-1",
            "from": {
                "id": 123456,
                "username": "sri",
                "first_name": "Sri",
            },
            "data": "market:yes",
            "message": {
                "message_id": 52,
                "chat": {
                    "id": 123456,
                },
            },
        },
    }

    result = parser.parse(update)

    assert result["update_type"] == "callback_query"
    assert result["callback_query_id"] == "callback-1"
    assert result["callback_data"] == "market:yes"
    assert result["telegram_user_id"] == 123456
    assert result["chat_id"] == 123456


def test_parse_unsupported_update():
    parser = TelegramParser()

    result = parser.parse(
        {
            "update_id": 1004,
            "edited_message": {},
        }
    )

    assert result["update_type"] == "unsupported"


def test_parser_rejects_non_dictionary():
    parser = TelegramParser()

    try:
        parser.parse("invalid")
    except TypeError as exc:
        assert "dictionary" in str(exc)
    else:
        raise AssertionError("Expected TypeError")