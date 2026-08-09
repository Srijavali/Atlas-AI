from io import BytesIO

import pytest
from PIL import Image

from backend.domain.exceptions import ImageProcessingError
from backend.modules.preprocessing.image_processor import ImageProcessor


def create_test_image() -> bytes:
    buffer = BytesIO()

    image = Image.new("RGB", (100, 100), "white")
    image.save(buffer, format="PNG")

    return buffer.getvalue()


@pytest.fixture
def processor() -> ImageProcessor:
    return ImageProcessor()


def test_processor_accepts_valid_png(processor: ImageProcessor):
    image = processor.validate(create_test_image())

    assert isinstance(image, Image.Image)
    assert image.mode == "RGB"
    assert image.size == (100, 100)


def test_processor_rejects_empty_bytes(processor: ImageProcessor):
    with pytest.raises(ImageProcessingError):
        processor.validate(b"")


def test_processor_rejects_invalid_image_bytes(
    processor: ImageProcessor,
):
    with pytest.raises(ImageProcessingError):
        processor.validate(b"this is not an image")


def test_processor_rejects_non_bytes_input(
    processor: ImageProcessor,
):
    with pytest.raises(TypeError):
        processor.validate("not bytes")  # type: ignore[arg-type]


def test_processor_returns_independent_image(
    processor: ImageProcessor,
):
    source = create_test_image()

    first = processor.validate(source)
    second = processor.validate(source)

    assert first is not second
    assert first.size == second.size


def test_processor_preserves_rgb_images(
    processor: ImageProcessor,
):
    image = Image.new("RGB", (100, 80), "white")

    prepared = processor.prepare(image)

    assert prepared.mode == "RGB"
    assert prepared.size == (100, 80)


def test_processor_converts_grayscale_to_rgb(
    processor: ImageProcessor,
):
    image = Image.new("L", (100, 80), 255)

    prepared = processor.prepare(image)

    assert prepared.mode == "RGB"
    assert prepared.size == (100, 80)


def test_processor_preserves_rgba_images(
    processor: ImageProcessor,
):
    image = Image.new("RGBA", (100, 80), (255, 255, 255, 128))

    prepared = processor.prepare(image)

    assert prepared.mode == "RGBA"
    assert prepared.size == (100, 80)


def test_processor_resizes_large_images(
    processor: ImageProcessor,
):
    image = Image.new("RGB", (4096, 2048), "white")

    prepared = processor.prepare(image)

    assert max(prepared.size) == 2048
    assert prepared.size == (2048, 1024)


def test_processor_does_not_upscale_small_images(
    processor: ImageProcessor,
):
    image = Image.new("RGB", (800, 600), "white")

    prepared = processor.prepare(image)

    assert prepared.size == (800, 600)


def test_processor_rejects_non_image_for_preparation(
    processor: ImageProcessor,
):
    with pytest.raises(TypeError):
        processor.prepare("not an image")  # type: ignore[arg-type]
    