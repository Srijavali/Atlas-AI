from typing import Any

from pydantic import BaseModel, Field


class ImageProcessingResult(BaseModel):
    """
    Canonical result produced after processing an image.

    OCR and vision outputs remain separate so downstream components
    can distinguish extracted text from visual interpretation.
    """

    ocr_text: str = Field(
        default="",
        description="Text physically extracted from the image",
    )

    vision_description: str = Field(
        default="",
        description="Description or interpretation produced from visual content",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Non-semantic metadata about image processing",
    )