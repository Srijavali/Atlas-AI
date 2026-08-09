import pytest
from pydantic import ValidationError

from backend.domain.models.preprocessing import (
    InputType,
    PreprocessedInput,
)


def test_preprocessed_input_accepts_valid_text():
    result = PreprocessedInput(
        text="What's Apple's stock price?",
        input_type=InputType.TEXT,
    )

    assert result.text == "What's Apple's stock price?"
    assert result.input_type == InputType.TEXT
    assert result.metadata == {}


def test_preprocessed_input_strips_outer_whitespace():
    result = PreprocessedInput(
        text="   Hello Atlas   ",
        input_type=InputType.TEXT,
    )

    assert result.text == "Hello Atlas"


def test_preprocessed_input_rejects_empty_text():
    with pytest.raises(ValidationError):
        PreprocessedInput(
            text="   ",
            input_type=InputType.TEXT,
        )


def test_preprocessed_input_accepts_metadata():
    result = PreprocessedInput(
        text="An NVIDIA stock chart showing upward movement.",
        input_type=InputType.IMAGE,
        metadata={
            "ocr_used": True,
            "vision_used": True,
        },
    )

    assert result.input_type == InputType.IMAGE
    assert result.metadata["ocr_used"] is True
    assert result.metadata["vision_used"] is True


def test_all_input_types_are_supported():
    expected = {
        "text",
        "image",
        "audio",
        "document",
    }

    actual = {input_type.value for input_type in InputType}

    assert actual == expected