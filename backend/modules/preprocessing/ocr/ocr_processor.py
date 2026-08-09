from abc import ABC, abstractmethod

from PIL import Image

from backend.domain.exceptions import OCRProcessingError


class OCRBackend(ABC):
    """Backend interface for OCR inference."""

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        """Extract textual content from an image."""
        raise NotImplementedError


class OCRProcessor:
    """
    Coordinates OCR processing without coupling Atlas to a
    specific OCR implementation.
    """

    def __init__(self, backend: OCRBackend):
        self._backend = backend

    def extract_text(self, image: Image.Image) -> str:
        """Extract text from a prepared image."""

        if not isinstance(image, Image.Image):
            raise TypeError("OCRProcessor expects a Pillow Image")

        try:
            return self._backend.extract_text(image)

        except OCRProcessingError:
            raise

        except Exception as exc:
            raise OCRProcessingError(
                "OCR backend failed during text extraction"
            ) from exc