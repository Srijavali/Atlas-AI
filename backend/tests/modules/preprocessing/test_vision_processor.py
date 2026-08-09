from io import BytesIO

import pytest
from PIL import Image

from backend.domain.exceptions import VisionProcessingError
from backend.modules.preprocessing.vision.vision_processor import (
    VisionBackend,
    VisionProcessor,
)


class FakeVisionBackend(VisionBackend):
    def __init__(self, description: str):
        self.description = description

    def describe(self, image: Image.Image) -> str:
        return self.description


class FailingVisionBackend(VisionBackend):
    def describe(self, image: Image.Image) -> str:
        raise RuntimeError("Simulated vision backend failure")


class DomainFailingVisionBackend(VisionBackend):
    def describe(self, image: Image.Image) -> str:
        raise VisionProcessingError("Vision unavailable")


def create_test_image() -> Image.Image:
    buffer = BytesIO()

    image = Image.new("RGB", (100, 100), "white")
    image.save(buffer, format="PNG")

    buffer.seek(0)

    return Image.open(buffer).copy()


def test_vision_processor_returns_backend_description():
    backend = FakeVisionBackend(
        "A white image containing black text."
    )

    processor = VisionProcessor(backend)

    result = processor.describe(create_test_image())

    assert result == "A white image containing black text."


def test_vision_processor_accepts_empty_backend_result():
    backend = FakeVisionBackend("")

    processor = VisionProcessor(backend)

    result = processor.describe(create_test_image())

    assert result == ""


def test_vision_processor_rejects_non_image_input():
    backend = FakeVisionBackend("description")

    processor = VisionProcessor(backend)

    with pytest.raises(TypeError) as exc_info:
        processor.describe("not an image")  # type: ignore[arg-type]

    assert str(exc_info.value) == (
        "VisionProcessor expects a Pillow Image"
    )


def test_vision_processor_wraps_backend_failure():
    backend = FailingVisionBackend()

    processor = VisionProcessor(backend)

    with pytest.raises(VisionProcessingError) as exc_info:
        processor.describe(create_test_image())

    assert str(exc_info.value) == (
        "Vision backend failed during image understanding"
    )

    assert exc_info.value.__cause__ is not None


def test_vision_processor_preserves_domain_error():
    backend = DomainFailingVisionBackend()

    processor = VisionProcessor(backend)

    with pytest.raises(VisionProcessingError) as exc_info:
        processor.describe(create_test_image())

    assert str(exc_info.value) == "Vision unavailable"