
from PIL import Image

from backend.domain.models.preprocessing import (
    InputType,
    PreprocessedInput,
)


class PreprocessingService:
    """
    Orchestrates the individual preprocessing components.

    The service coordinates modality-specific processors and converts
    their outputs into the canonical PreprocessedInput contract.
    """

    def __init__(
        self,
        *,
        text_normalizer,
        image_processor,
        ocr_processor,
        vision_processor,
        document_processor,
        speech_processor,
    ):
        self._text_normalizer = text_normalizer
        self._image_processor = image_processor
        self._ocr_processor = ocr_processor
        self._vision_processor = vision_processor
        self._document_processor = document_processor
        self._speech_processor = speech_processor

    def process_text(self, text: str) -> PreprocessedInput:
        normalized_text = self._text_normalizer.normalize(text)

        return PreprocessedInput(
            text=normalized_text,
            input_type=InputType.TEXT,
        )

    def process_document(
        self,
        content: bytes,
        *,
        filename: str,
    ) -> PreprocessedInput:
        return self._document_processor.process(
            content,
            filename=filename,
        )

    def process_audio(
        self,
        content: bytes,
        *,
        filename: str,
    ) -> PreprocessedInput:
        return self._speech_processor.process(
            content,
            filename=filename,
        )

    def process_image_for_ocr(
        self,
        image_bytes: bytes,
    ) -> PreprocessedInput:
        image = self._image_processor.validate(image_bytes)
        prepared_image = self._image_processor.prepare(image)

        text = self._ocr_processor.extract_text(prepared_image)

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Preprocessed text cannot be empty")

        return PreprocessedInput(
            text=text,
            input_type=InputType.IMAGE,
        )

    def process_image_for_vision(
        self,
        image_bytes: bytes,
    ) -> PreprocessedInput:
        image = self._image_processor.validate(image_bytes)
        prepared_image = self._image_processor.prepare(image)

        text = self._vision_processor.describe(prepared_image)

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Preprocessed text cannot be empty")

        return PreprocessedInput(
            text=text,
            input_type=InputType.IMAGE,
        )

