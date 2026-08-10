from __future__ import annotations

from io import BytesIO

from groq import AsyncGroq

from backend.configuration.settings import settings
from backend.infrastructure.llm.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
)


class GroqSpeechToText:
    """
    Speech-to-text adapter backed by Groq Whisper.

    Telegram/media concerns remain outside this class.
    This class only converts audio bytes into text.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = (
            api_key
            or settings.GROQ_API_KEY
        ).strip()

        self._model = (
            model
            or getattr(
                settings,
                "GROQ_SPEECH_MODEL",
                "whisper-large-v3-turbo",
            )
        )

        if not self._api_key:
            raise LLMProviderError(
                "Groq API key is not configured"
            )

        try:
            self._client = AsyncGroq(
                api_key=self._api_key
            )
        except Exception as exc:
            raise LLMProviderError(
                "Failed to initialize Groq speech client"
            ) from exc

    async def transcribe(
        self,
        *,
        audio: bytes,
        filename: str = "voice.ogg",
        language: str | None = None,
    ) -> str:
        """
        Transcribe audio bytes into text.
        """

        if not isinstance(audio, bytes):
            raise TypeError(
                "Audio content must be bytes"
            )

        if not audio:
            raise ValueError(
                "Audio content cannot be empty"
            )

        try:
            audio_file = BytesIO(audio)

            transcription = (
                await self._client.audio.transcriptions.create(
                    file=(
                        filename,
                        audio_file,
                    ),
                    model=self._model,
                    language=language,
                    response_format="json",
                    temperature=0.0,
                )
            )

        except Exception as exc:
            status_code = getattr(
                exc,
                "status_code",
                None,
            )

            message = str(exc).lower()

            if (
                status_code == 429
                or "rate limit" in message
                or "rate_limit" in message
                or "quota" in message
            ):
                raise LLMRateLimitError(
                    "Groq speech-to-text rate limit "
                    "or quota exceeded"
                ) from exc

            raise LLMProviderError(
                "Groq speech-to-text failed"
            ) from exc

        text = getattr(
            transcription,
            "text",
            None,
        )

        if not isinstance(text, str) or not text.strip():
            raise LLMProviderError(
                "Groq speech-to-text returned empty text"
            )

        return text.strip()