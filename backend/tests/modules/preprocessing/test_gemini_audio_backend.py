
from unittest.mock import Mock

import pytest

from backend.modules.preprocessing.voice.gemini_audio_backend import (
    GeminiAudioBackend,
)


@pytest.fixture
def client():
    return Mock()


@pytest.fixture
def backend(client):
    return GeminiAudioBackend(client=client)


def test_backend_transcribes_audio(client, backend):
    response = Mock()
    response.text = "Hello Atlas AI"
    client.models.generate_content.return_value = response

    result = backend.transcribe(
        b"fake-audio-data",
        filename="voice.wav",
    )

    assert result == "Hello Atlas AI"
    client.models.generate_content.assert_called_once()



def test_backend_uses_audio_mime_type(client, backend):
    response = Mock()
    response.text = "Hello Atlas"
    client.models.generate_content.return_value = response

    backend.transcribe(
        b"fake-audio-data",
        filename="voice.wav",
    )

    call = client.models.generate_content.call_args
    contents = call.kwargs["contents"]

    audio_part = contents[1]

    assert audio_part.inline_data.data == b"fake-audio-data"
    assert audio_part.inline_data.mime_type == "audio/wav"





def test_backend_supports_mp3(client, backend):
    response = Mock()
    response.text = "Hello Atlas"
    client.models.generate_content.return_value = response

    backend.transcribe(
        b"fake-audio-data",
        filename="voice.mp3",
    )

    call = client.models.generate_content.call_args
    contents = call.kwargs["contents"]

    audio_part = contents[1]

    assert audio_part.inline_data.mime_type == "audio/mpeg"



def test_backend_rejects_unsupported_audio_format(backend):
    with pytest.raises(
        ValueError,
        match="Unsupported audio format",
    ):
        backend.transcribe(
            b"fake-audio-data",
            filename="voice.xyz",
        )


def test_backend_rejects_empty_audio(backend):
    with pytest.raises(
        ValueError,
        match="Audio content cannot be empty",
    ):
        backend.transcribe(
            b"",
            filename="voice.wav",
        )


def test_backend_translates_api_error(client, backend):
    client.models.generate_content.side_effect = RuntimeError(
        "API failure"
    )

    with pytest.raises(
        RuntimeError,
        match="Gemini audio transcription failed",
    ):
        backend.transcribe(
            b"fake-audio-data",
            filename="voice.wav",
        )


def test_backend_rejects_empty_response(client, backend):
    response = Mock()
    response.text = None
    client.models.generate_content.return_value = response

    with pytest.raises(
        ValueError,
        match="Gemini returned an empty transcription",
    ):
        backend.transcribe(
            b"fake-audio-data",
            filename="voice.wav",
        )

