
from pathlib import Path

from google import genai
from google.genai import types


class GeminiAudioBackend:
    """Gemini-backed audio transcription service."""

    MODEL_NAME = "gemini-2.5-flash"

    MIME_TYPES = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }

    def __init__(self, client=None):
        try:
            self._client = client or genai.Client()
        except Exception as exc:
            raise RuntimeError(
                "Failed to initialize Gemini audio client"
            ) from exc

    def transcribe(
        self,
        content: bytes,
        *,
        filename: str,
    ) -> str:
        if not isinstance(content, bytes):
            raise TypeError("GeminiAudioBackend expects bytes")

        if not content:
            raise ValueError("Audio content cannot be empty")

        extension = Path(filename).suffix.lower()
        mime_type = self.MIME_TYPES.get(extension)

        if mime_type is None:
            raise ValueError(
                f"Unsupported audio format: {extension or 'unknown'}"
            )

        audio_part = types.Part.from_bytes(
            data=content,
            mime_type=mime_type,
        )

        try:
            response = self._client.models.generate_content(
                model=self.MODEL_NAME,
                contents=[
                    "Transcribe the spoken audio exactly. "
                    "Return only the transcription text.",
                    audio_part,
                ],
            )
        except Exception as exc:
            raise RuntimeError(
                "Gemini audio transcription failed"
            ) from exc

        text = response.text

        if not text or not text.strip():
            raise ValueError(
                "Gemini returned an empty transcription"
            )

        return text.strip()

