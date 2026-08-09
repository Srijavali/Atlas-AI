
from unittest.mock import Mock

import pytest
from PIL import Image

from backend.domain.models.preprocessing import (
    InputType,
    PreprocessedInput,
)
from backend.modules.preprocessing.service import PreprocessingService


@pytest.fixture
def text_normalizer():
    return Mock()


@pytest.fixture
def image_processor():
    return Mock()


@pytest.fixture
def ocr_processor():
    return Mock()


@pytest.fixture
def vision_processor():
    return Mock()


@pytest.fixture
def document_processor():
    return Mock()


@pytest.fixture
def speech_processor():
    return Mock()


@pytest.fixture
def service(
    text_normalizer,
    image_processor,
    ocr_processor,
    vision_processor,
    document_processor,
    speech_processor,
):
    return PreprocessingService(
        text_normalizer=text_normalizer,
        image_processor=image_processor,
        ocr_processor=ocr_processor,
        vision_processor=vision_processor,
        document_processor=document_processor,
        speech_processor=speech_processor,
    )


def test_process_text_returns_preprocessed_input(
    service,
    text_normalizer,
):
    text_normalizer.normalize.return_value = "Hello Atlas"

    result = service.process_text("  Hello Atlas  ")

    assert isinstance(result, PreprocessedInput)
    assert result.text == "Hello Atlas"
    assert result.input_type == InputType.TEXT

    text_normalizer.normalize.assert_called_once_with(
        "  Hello Atlas  "
    )


def test_process_document_delegates_to_document_processor(
    service,
    document_processor,
):
    expected = PreprocessedInput(
        text="Document text",
        input_type=InputType.DOCUMENT,
        metadata={"filename": "test.pdf"},
    )

    document_processor.process.return_value = expected

    result = service.process_document(
        b"pdf-data",
        filename="test.pdf",
    )

    assert result is expected

    document_processor.process.assert_called_once_with(
        b"pdf-data",
        filename="test.pdf",
    )


def test_process_audio_delegates_to_speech_processor(
    service,
    speech_processor,
):
    expected = PreprocessedInput(
        text="Audio transcript",
        input_type=InputType.AUDIO,
        metadata={"filename": "voice.wav"},
    )

    speech_processor.process.return_value = expected

    result = service.process_audio(
        b"audio-data",
        filename="voice.wav",
    )

    assert result is expected

    speech_processor.process.assert_called_once_with(
        b"audio-data",
        filename="voice.wav",
    )


def test_process_image_for_ocr(
    service,
    image_processor,
    ocr_processor,
):
    image = Mock(spec=Image.Image)

    image_processor.validate.return_value = image
    image_processor.prepare.return_value = image
    ocr_processor.extract_text.return_value = "Text from image"

    result = service.process_image_for_ocr(
        b"image-data",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.text == "Text from image"
    assert result.input_type == InputType.IMAGE

    image_processor.validate.assert_called_once_with(
        b"image-data"
    )
    image_processor.prepare.assert_called_once_with(image)
    ocr_processor.extract_text.assert_called_once_with(image)


def test_process_image_for_vision(
    service,
    image_processor,
    vision_processor,
):
    image = Mock(spec=Image.Image)

    image_processor.validate.return_value = image
    image_processor.prepare.return_value = image
    vision_processor.describe.return_value = "A photo of a document"

    result = service.process_image_for_vision(
        b"image-data",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.text == "A photo of a document"
    assert result.input_type == InputType.IMAGE

    image_processor.validate.assert_called_once_with(
        b"image-data"
    )
    image_processor.prepare.assert_called_once_with(image)
    vision_processor.describe.assert_called_once_with(image)


def test_process_text_rejects_empty_normalized_result(
    service,
    text_normalizer,
):
    text_normalizer.normalize.side_effect = ValueError(
        "Normalized text cannot be empty"
    )

    with pytest.raises(
        ValueError,
        match="Normalized text cannot be empty",
    ):
        service.process_text("   ")


def test_process_image_for_ocr_rejects_empty_result(
    service,
    image_processor,
    ocr_processor,
):
    image = Mock(spec=Image.Image)

    image_processor.validate.return_value = image
    image_processor.prepare.return_value = image
    ocr_processor.extract_text.return_value = "   "

    with pytest.raises(
        ValueError,
        match="Preprocessed text cannot be empty",
    ):
        service.process_image_for_ocr(b"image-data")

