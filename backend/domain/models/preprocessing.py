from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class InputType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"


class PreprocessedInput(BaseModel):
    """
    Canonical representation produced by the Input Preprocessor.

    Every supported input modality must eventually produce textual
    content through this contract.
    """

    text: str = Field(
        min_length=1,
        description="Normalized textual representation of the input",
    )

    input_type: InputType = Field(
        description="Original modality of the input",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Non-semantic metadata produced during preprocessing",
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Preprocessed text cannot be empty")

        return value