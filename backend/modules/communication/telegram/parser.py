from typing import Any


class TelegramParser:
    """Parse Telegram webhook updates into Telegram-specific data."""

    def parse(self, update: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(update, dict):
            raise TypeError("Telegram update must be a dictionary")

        result: dict[str, Any] = {
            "platform_event_id": (
                str(update["update_id"])
                if update.get("update_id") is not None
                else None
            ),
            "telegram_user_id": None,
            "username": None,
            "first_name": None,
            "chat_id": None,
            "message_id": None,
            "command": None,
            "text": None,
            "callback_data": None,
            "callback_query_id": None,

            # Multimodal fields
            "media_reference": None,
            "media_type": None,
            "filename": None,
            "mime_type": None,

            "update_type": "unsupported",
        }

        # ============================================================
        # NORMAL TELEGRAM MESSAGE
        # ============================================================

        if "message" in update:
            message = update.get("message") or {}

            result["update_type"] = "message"
            result["message_id"] = message.get("message_id")

            chat = message.get("chat") or {}
            result["chat_id"] = chat.get("id")

            user = message.get("from") or {}
            result["telegram_user_id"] = user.get("id")
            result["username"] = user.get("username")
            result["first_name"] = user.get("first_name")

            # --------------------------------------------------------
            # Plain text / caption
            # --------------------------------------------------------

            text = message.get("text")

            if text is None:
                text = message.get("caption")

            result["text"] = text

            if isinstance(text, str) and text.startswith("/"):
                result["command"] = text.split()[0]

            # --------------------------------------------------------
            # Document
            # --------------------------------------------------------

            document = message.get("document")

            if isinstance(document, dict):
                result["media_type"] = "document"
                result["media_reference"] = document.get("file_id")
                result["filename"] = (
                    document.get("file_name")
                    or f"document_{message.get('message_id', 'unknown')}"
                )
                result["mime_type"] = document.get("mime_type")

            # --------------------------------------------------------
            # Voice message
            # --------------------------------------------------------

            voice = message.get("voice")

            if isinstance(voice, dict):
                result["media_type"] = "voice"
                result["media_reference"] = voice.get("file_id")
                result["filename"] = (
                    f"voice_{message.get('message_id', 'unknown')}.ogg"
                )
                result["mime_type"] = (
                    voice.get("mime_type")
                    or "audio/ogg"
                )

            # --------------------------------------------------------
            # Audio file
            # --------------------------------------------------------

            audio = message.get("audio")

            if isinstance(audio, dict):
                result["media_type"] = "audio"
                result["media_reference"] = audio.get("file_id")
                result["filename"] = (
                    audio.get("file_name")
                    or f"audio_{message.get('message_id', 'unknown')}.mp3"
                )
                result["mime_type"] = audio.get("mime_type")

            # --------------------------------------------------------
            # Image / Telegram photo
            #
            # Telegram provides multiple resolutions.
            # The last photo is normally the largest available size.
            # --------------------------------------------------------

            photos = message.get("photo")

            if isinstance(photos, list) and photos:
                photo = photos[-1]

                if isinstance(photo, dict):
                    result["media_type"] = "image"
                    result["media_reference"] = photo.get("file_id")
                    result["filename"] = (
                        f"image_{message.get('message_id', 'unknown')}.jpg"
                    )
                    result["mime_type"] = "image/jpeg"

        # ============================================================
        # INLINE KEYBOARD CALLBACK
        # ============================================================

        elif "callback_query" in update:
            callback = update.get("callback_query") or {}

            result["update_type"] = "callback_query"
            result["callback_query_id"] = callback.get("id")
            result["callback_data"] = callback.get("data")

            user = callback.get("from") or {}
            result["telegram_user_id"] = user.get("id")
            result["username"] = user.get("username")
            result["first_name"] = user.get("first_name")

            message = callback.get("message") or {}
            result["message_id"] = message.get("message_id")

            chat = message.get("chat") or {}
            result["chat_id"] = chat.get("id")

        return result