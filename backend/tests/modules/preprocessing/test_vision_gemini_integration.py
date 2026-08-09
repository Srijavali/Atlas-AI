from dotenv import load_dotenv

load_dotenv()
import pytest
from io import BytesIO

from PIL import Image

from backend.modules.preprocessing.vision.gemini_backend import (
    GeminiVisionBackend,
)
from backend.modules.preprocessing.vision.vision_processor import (
    VisionProcessor,
)


def create_test_image() -> Image.Image:
    buffer = BytesIO()

    image = Image.new("RGB", (400, 200), "white")
    image.save(buffer, format="PNG")

    buffer.seek(0)

    return Image.open(buffer).copy()


@pytest.mark.integration
def test_vision_processor_works_with_gemini_backend():
    backend = GeminiVisionBackend()
    processor = VisionProcessor(backend)

    result = processor.describe(create_test_image())

    assert isinstance(result, str)
    assert result.strip()

