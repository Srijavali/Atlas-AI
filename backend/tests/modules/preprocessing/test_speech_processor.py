
from unittest.mock import Mock

import pytest

from backend.domain.models.preprocessing import InputType, PreprocessedInput
from backend.modules.preprocessing.voice.speech_processor import (
    SpeechProcessor,
)


@pytest.fixture
def backend():
    return Mock()


@pytest.fixture
def processor(backend):
    return SpeechProcessor(backend)


def test_processor_transcribes_valid_audio(processor, backend):
    backend.transcribe.return_value = "Hello Atlas AI"

    result = processor.process(
        b"fake-audio-data",
        filename="voice.wav",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.text == "Hello Atlas AI"
    assert result.input_type == InputType.AUDIO


def test_processor_strips_transcript_whitespace(processor, backend):
    backend.transcribe.return_value = "   Hello Atlas   "

    result = processor.process(
        b"fake-audio-data",
        filename="voice.wav",
    )

    assert result.text == "Hello Atlas"


def test_processor_rejects_empty_audio(processor):
    with pytest.raises(ValueError, match="Audio content cannot be empty"):
        processor.process(
            b"",
            filename="voice.wav",
        )


def test_processor_rejects_unsupported_format(processor):
    with pytest.raises(ValueError, match="Unsupported audio format"):
        processor.process(
            b"fake-audio-data",
            filename="voice.xyz",
        )


def test_processor_rejects_non_bytes_input(processor):
    with pytest.raises(TypeError, match="expects bytes"):
        processor.process(
            "not bytes",  # type: ignore[arg-type]
            filename="voice.wav",
        )


def test_processor_preserves_audio_metadata(processor, backend):
    backend.transcribe.return_value = "Hello Atlas"

    result = processor.process(
        b"fake-audio-data",
        filename="meeting.wav",
    )

    assert result.metadata["filename"] == "meeting.wav"
    assert result.metadata["extension"] == ".wav"


def test_processor_rejects_empty_transcription(processor, backend):
    backend.transcribe.return_value = "   "

    with pytest.raises(ValueError, match="Transcription cannot be empty"):
        processor.process(
            b"fake-audio-data",
            filename="voice.wav",
        )


def test_processor_translates_backend_error(processor, backend):
    backend.transcribe.side_effect = RuntimeError("transcription failed")

    with pytest.raises(
        RuntimeError,
        match="Speech transcription failed",
    ):
        processor.process(
            b"fake-audio-data",
            filename="voice.wav",
        )

