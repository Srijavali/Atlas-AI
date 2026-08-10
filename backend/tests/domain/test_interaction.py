from datetime import datetime, timezone

from backend.domain.enums import InteractionType, Platform
from backend.domain.models.interaction import IncomingInteraction


def test_incoming_interaction_accepts_text_message():
    interaction = IncomingInteraction(
        interaction_id="interaction-1",
        platform=Platform.TELEGRAM,
        platform_event_id="telegram-update-1",
        user_id="123456789",
        conversation_id="987654321",
        interaction_type=InteractionType.TEXT,
        text="Hello Atlas",
    )

    assert interaction.platform == Platform.TELEGRAM
    assert interaction.interaction_type == InteractionType.TEXT
    assert interaction.user_id == "123456789"
    assert interaction.conversation_id == "987654321"
    assert interaction.text == "Hello Atlas"


def test_incoming_interaction_generates_timestamp():
    interaction = IncomingInteraction(
        interaction_id="interaction-2",
        platform=Platform.TELEGRAM,
        user_id="123456789",
        conversation_id="987654321",
        interaction_type=InteractionType.COMMAND,
        text="/start",
    )

    assert isinstance(interaction.timestamp, datetime)
    assert interaction.timestamp.tzinfo is not None


def test_incoming_interaction_defaults_metadata_to_empty_dict():
    interaction = IncomingInteraction(
        interaction_id="interaction-3",
        platform=Platform.TELEGRAM,
        user_id="123456789",
        conversation_id="987654321",
        interaction_type=InteractionType.TEXT,
    )

    assert interaction.metadata == {}