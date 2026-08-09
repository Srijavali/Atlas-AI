from io import BytesIO

from PIL import Image

from backend.modules.preprocessing.ocr.paddle_backend import (
    PaddleOCRBackend,
    PaddleOCRConfig,
)


def create_test_image() -> Image.Image:
    buffer = BytesIO()

    image = Image.new("RGB", (100, 100), "white")
    image.save(buffer, format="PNG")

    buffer.seek(0)

    return Image.open(buffer).copy()


def test_backend_configuration_uses_mobile_models():
    config = PaddleOCRConfig()

    assert config.text_detection_model_name == (
        "PP-OCRv5_mobile_det"
    )
    assert config.text_recognition_model_name == (
        "PP-OCRv5_mobile_rec"
    )

    assert config.use_doc_orientation_classify is False
    assert config.use_doc_unwarping is False
    assert config.use_textline_orientation is False


def test_backend_rejects_non_image_input():
    backend = PaddleOCRBackend()

    try:
        backend.extract_text("not an image")  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "PaddleOCRBackend expects a Pillow Image"
    else:
        raise AssertionError("Expected TypeError")


def test_backend_initializes():
    backend = PaddleOCRBackend()

    assert backend is not None


def test_backend_accepts_pillow_image():
    backend = PaddleOCRBackend()

    result = backend.extract_text(create_test_image())

    assert isinstance(result, str)