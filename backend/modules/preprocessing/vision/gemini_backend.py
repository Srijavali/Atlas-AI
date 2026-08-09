from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from google import genai
from google.genai import types
from PIL import Image

from backend.domain.exceptions import VisionProcessingError
from backend.modules.preprocessing.vision.vision_processor import VisionBackend


@dataclass(slots=True)
class GeminiVisionConfig:
    model: str = "gemini-2.5-flash"
    prompt: str = (
        "Describe the important visual content of this image. "
        "Focus on objects, people, scene, visible text, and relevant "
        "context. Be concise and factual."
    )


class GeminiVisionBackend(VisionBackend):
    """Gemini-backed implementation of the Atlas VisionBackend."""

    def __init__(
        self,
        config: GeminiVisionConfig | None = None,
        client: genai.Client | None = None,
    ) -> None:
        self._config = config or GeminiVisionConfig()

        try:
            self._client = client or genai.Client()
        except Exception as exc:
            raise VisionProcessingError(
                "Failed to initialize Gemini Vision client"
            ) from exc

    def describe(self, image: Image.Image) -> str:
        if not isinstance(image, Image.Image):
            raise TypeError(
                "GeminiVisionBackend expects a Pillow Image"
            )

        try:
            buffer = BytesIO()
            image.save(buffer, format="PNG")

            image_part = types.Part.from_bytes(
                data=buffer.getvalue(),
                mime_type="image/png",
            )

            response = self._client.models.generate_content(
                model=self._config.model,
                contents=[
                    self._config.prompt,
                    image_part,
                ],
            )

            text = response.text

            if not text or not text.strip():
                raise VisionProcessingError(
                    "Gemini returned an empty vision response"
                )

            return text.strip()

        except VisionProcessingError:
            raise

        except Exception as exc:
            raise VisionProcessingError(
                "Gemini Vision request failed"
            ) from exc