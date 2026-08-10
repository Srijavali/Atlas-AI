from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.domain.enums import InteractionType, Platform
from backend.domain.models.interaction import IncomingInteraction


class TelegramAdapter:
    """Convert parsed Telegram data into a platform-neutral interaction."""

    def adapt(
        self,
        parsed: dict[str, Any],
    ) -> IncomingInteraction:

        telegram_user_id = parsed.get(
            "telegram_user_id"
        )

        chat_id = parsed.get(
            "chat_id"
        )

        if telegram_user_id is None:
            raise ValueError(
                "Telegram interaction is missing user ID"
            )

        if chat_id is None:
            raise ValueError(
                "Telegram interaction is missing chat ID"
            )

        update_type = parsed.get(
            "update_type"
        )

        media_type = parsed.get(
            "media_type"
        )

        # ============================================================
        # DETERMINE INTERACTION TYPE
        # ============================================================

        if update_type == "callback_query":
            interaction_type = InteractionType.BUTTON

        elif parsed.get("command"):
            interaction_type = InteractionType.COMMAND

        elif media_type == "document":
            interaction_type = InteractionType.DOCUMENT

        elif media_type in {"voice", "audio"}:
            interaction_type = InteractionType.VOICE

        elif media_type == "image":
            interaction_type = InteractionType.IMAGE

        elif update_type == "message":
            interaction_type = InteractionType.TEXT

        else:
            raise ValueError(
                f"Unsupported Telegram update type: {update_type}"
            )

        # ============================================================
        # BUILD PLATFORM-NEUTRAL INTERACTION
        # ============================================================

        return IncomingInteraction(
            interaction_id=str(uuid4()),
            platform=Platform.TELEGRAM,
            platform_event_id=parsed.get(
                "platform_event_id"
            ),
            user_id=str(
                telegram_user_id
            ),
            conversation_id=str(
                chat_id
            ),
            interaction_type=interaction_type,
            timestamp=datetime.now(timezone.utc),
            text=parsed.get("text"),
            media_reference=parsed.get(
                "media_reference"
            ),
            metadata={
                "telegram_user_id": telegram_user_id,
                "username": parsed.get("username"),
                "first_name": parsed.get("first_name"),
                "chat_id": chat_id,
                "message_id": parsed.get("message_id"),
                "command": parsed.get("command"),
                "callback_data": parsed.get("callback_data"),
                "callback_query_id": parsed.get(
                    "callback_query_id"
                ),

                # Multimodal metadata
                "media_type": media_type,
                "filename": parsed.get("filename"),
                "mime_type": parsed.get("mime_type"),
            },
        )