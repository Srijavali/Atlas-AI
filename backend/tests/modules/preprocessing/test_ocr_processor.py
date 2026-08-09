from io import BytesIO

from PIL import Image

from backend.modules.preprocessing.ocr.ocr_processor import (
    OCRBackend,
    OCRProcessor,
)

import pytest

from backend.domain.exceptions import OCRProcessingError

class FailingOCRBackend(OCRBackend):
    def extract_text(self, image: Image.Image) -> str:
        raise RuntimeError("Simulated Paddle runtime failure")


def test_ocr_processor_wraps_backend_failure():
    backend = FailingOCRBackend()
    processor = OCRProcessor(backend)

    with pytest.raises(OCRProcessingError) as exc_info:
        processor.extract_text(create_test_image())

    assert str(exc_info.value) == (
        "OCR backend failed during text extraction"
    )

    assert exc_info.value.__cause__ is not None

class DomainFailingOCRBackend(OCRBackend):
    def extract_text(self, image: Image.Image) -> str:
        raise OCRProcessingError("OCR unavailable")


def test_ocr_processor_preserves_ocr_processing_error():
    backend = DomainFailingOCRBackend()
    processor = OCRProcessor(backend)

    with pytest.raises(OCRProcessingError) as exc_info:
        processor.extract_text(create_test_image())

    assert str(exc_info.value) == "OCR unavailable"


class FakeOCRBackend(OCRBackend):
    def __init__(self, text: str):
        self.text = text

    def extract_text(self, image: Image.Image) -> str:
        return self.text


def create_test_image() -> Image.Image:
    buffer = BytesIO()

    image = Image.new("RGB", (100, 100), "white")
    image.save(buffer, format="PNG")

    buffer.seek(0)

    return Image.open(buffer).copy()


def test_ocr_processor_returns_backend_text():
    backend = FakeOCRBackend("Hello Atlas")
    processor = OCRProcessor(backend)

    result = processor.extract_text(create_test_image())

    assert result == "Hello Atlas"


def test_ocr_processor_accepts_empty_backend_result():
    backend = FakeOCRBackend("")
    processor = OCRProcessor(backend)

    result = processor.extract_text(create_test_image())

    assert result == ""


def test_ocr_processor_rejects_non_image_input():
    backend = FakeOCRBackend("Hello Atlas")
    processor = OCRProcessor(backend)

    try:
        processor.extract_text(b"not an image")
    except TypeError as exc:
        assert str(exc) == "OCRProcessor expects a Pillow Image"
    else:
        raise AssertionError("Expected TypeError")


def test_ocr_backend_is_replaceable():
    first = OCRProcessor(FakeOCRBackend("First result"))
    second = OCRProcessor(FakeOCRBackend("Second result"))

    image = create_test_image()

    assert first.extract_text(image) == "First result"
    assert second.extract_text(image) == "Second result"