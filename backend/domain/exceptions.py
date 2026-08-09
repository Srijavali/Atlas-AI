class ImageProcessingError(Exception):
    """Raised when an image cannot be safely processed."""


class OCRProcessingError(Exception):
    """Raised when OCR processing cannot be completed."""

class VisionProcessingError(Exception):
    """Raised when visual understanding cannot be completed."""