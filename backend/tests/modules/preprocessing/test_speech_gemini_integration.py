from unittest.mock import Mock

from backend.domain.models.preprocessing import (
    InputType,
    PreprocessedInput,
)
from backend.modules.preprocessing.voice.gemini_audio_backend import (
    GeminiAudioBackend,
)
from backend.modules.preprocessing.voice.speech_processor import (
    SpeechProcessor,
)


def test_speech_processor_works_with_gemini_backend():
    client = Mock()

    response = Mock()
    response.text = "Hello from Atlas"

    client.models.generate_content.return_value = response

    backend = GeminiAudioBackend(client=client)
    processor = SpeechProcessor(backend)

    result = processor.process(
        b"fake-audio-data",
        filename="voice.wav",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.text == "Hello from Atlas"
    assert result.input_type == InputType.AUDIO

    client.models.generate_content.assert_called_once()