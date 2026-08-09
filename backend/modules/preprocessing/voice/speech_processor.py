
from pathlib import Path

from backend.domain.models.preprocessing import (
    InputType,
    PreprocessedInput,
)


class SpeechProcessor:
    """Convert supported audio input into canonical text."""

    SUPPORTED_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".ogg",
        ".flac",
    }

    def __init__(self, backend):
        self._backend = backend

    def process(
        self,
        content: bytes,
        *,
        filename: str,
    ) -> PreprocessedInput:
        if not isinstance(content, bytes):
            raise TypeError("SpeechProcessor expects bytes")

        if not content:
            raise ValueError("Audio content cannot be empty")

        extension = Path(filename).suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio format: {extension or 'unknown'}"
            )

        try:
            transcript = self._backend.transcribe(
                content,
                filename=filename,
            )
        except Exception as exc:
            raise RuntimeError("Speech transcription failed") from exc

        transcript = transcript.strip()

        if not transcript:
            raise ValueError("Transcription cannot be empty")

        return PreprocessedInput(
            text=transcript,
            input_type=InputType.AUDIO,
            metadata={
                "filename": filename,
                "extension": extension,
            },
        )

