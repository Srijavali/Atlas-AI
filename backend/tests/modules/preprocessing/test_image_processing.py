from backend.domain.models.image_processing import ImageProcessingResult


def test_image_processing_result_defaults_to_empty_outputs():
    result = ImageProcessingResult()

    assert result.ocr_text == ""
    assert result.vision_description == ""
    assert result.metadata == {}


def test_image_processing_result_accepts_ocr_output():
    result = ImageProcessingResult(
        ocr_text="NVIDIA 182.30 +4.7%",
    )

    assert result.ocr_text == "NVIDIA 182.30 +4.7%"
    assert result.vision_description == ""


def test_image_processing_result_accepts_vision_output():
    result = ImageProcessingResult(
        vision_description="A stock chart showing upward movement.",
    )

    assert result.vision_description == (
        "A stock chart showing upward movement."
    )
    assert result.ocr_text == ""


def test_image_processing_result_keeps_ocr_and_vision_separate():
    result = ImageProcessingResult(
        ocr_text="NVIDIA 182.30",
        vision_description="A stock chart showing upward movement.",
    )

    assert result.ocr_text == "NVIDIA 182.30"
    assert result.vision_description == (
        "A stock chart showing upward movement."
    )


def test_image_processing_result_accepts_metadata():
    result = ImageProcessingResult(
        ocr_text="Hello",
        metadata={
            "format": "JPEG",
            "width": 1920,
            "height": 1080,
        },
    )

    assert result.metadata["format"] == "JPEG"
    assert result.metadata["width"] == 1920



