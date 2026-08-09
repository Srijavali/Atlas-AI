from abc import ABC, abstractmethod

from PIL import Image

from backend.domain.exceptions import VisionProcessingError


class VisionBackend(ABC):
    """Backend interface for visual understanding."""

    @abstractmethod
    def describe(self, image: Image.Image) -> str:
        """Generate a textual description of the visual content."""
        raise NotImplementedError


class VisionProcessor:
    """
    Coordinates visual understanding without coupling Atlas
    to a specific vision model.
    """

    def __init__(self, backend: VisionBackend):
        self._backend = backend

    def describe(self, image: Image.Image) -> str:
        """Generate a textual description from a prepared image."""

        if not isinstance(image, Image.Image):
            raise TypeError("VisionProcessor expects a Pillow Image")

        try:
            return self._backend.describe(image)

        except VisionProcessingError:
            raise

        except Exception as exc:
            raise VisionProcessingError(
                "Vision backend failed during image understanding"
            ) from exc