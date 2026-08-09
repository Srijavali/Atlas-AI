from io import BytesIO

import pytest
from PIL import Image

from backend.domain.exceptions import VisionProcessingError
from backend.modules.preprocessing.vision.gemini_backend import (
    GeminiVisionBackend,
    GeminiVisionConfig,
)


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)

        if self.error:
            raise self.error

        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.models = FakeModels(
            response=response,
            error=error,
        )


def create_test_image() -> Image.Image:
    buffer = BytesIO()

    image = Image.new("RGB", (100, 100), "white")
    image.save(buffer, format="PNG")

    buffer.seek(0)

    return Image.open(buffer).copy()


def test_backend_returns_gemini_description():
    client = FakeClient(
        response=FakeResponse(
            "A white image containing black text."
        )
    )

    backend = GeminiVisionBackend(client=client)

    result = backend.describe(create_test_image())

    assert result == "A white image containing black text."

    assert len(client.models.calls) == 1


def test_backend_uses_configured_model():
    client = FakeClient(
        response=FakeResponse("Image description")
    )

    config = GeminiVisionConfig(
        model="test-vision-model"
    )

    backend = GeminiVisionBackend(
        config=config,
        client=client,
    )

    backend.describe(create_test_image())

    call = client.models.calls[0]

    assert call["model"] == "test-vision-model"


def test_backend_rejects_non_image_input():
    client = FakeClient()

    backend = GeminiVisionBackend(client=client)

    with pytest.raises(TypeError) as exc_info:
        backend.describe("not an image")  # type: ignore[arg-type]

    assert str(exc_info.value) == (
        "GeminiVisionBackend expects a Pillow Image"
    )


def test_backend_wraps_api_failure():
    client = FakeClient(
        error=RuntimeError("simulated API failure")
    )

    backend = GeminiVisionBackend(client=client)

    with pytest.raises(VisionProcessingError) as exc_info:
        backend.describe(create_test_image())

    assert str(exc_info.value) == (
        "Gemini Vision request failed"
    )

    assert exc_info.value.__cause__ is not None


def test_backend_rejects_empty_response():
    client = FakeClient(
        response=FakeResponse("")
    )

    backend = GeminiVisionBackend(client=client)

    with pytest.raises(VisionProcessingError) as exc_info:
        backend.describe(create_test_image())

    assert str(exc_info.value) == (
        "Gemini returned an empty vision response"
    )