from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from backend.domain.exceptions import ImageProcessingError


class ImageProcessor:
    """
    Handles deterministic image validation and preparation.

    Model inference such as OCR and visual understanding belongs
    to the dedicated OCR and Vision processors.
    """

    MAX_IMAGE_DIMENSION = 2048

    def validate(self, image_bytes: bytes) -> Image.Image:
        """
        Validate image bytes and return a readable Pillow image.

        Raises:
            TypeError: If input is not bytes.
            ImageProcessingError: If the bytes do not represent
                a readable image.
        """
        if not isinstance(image_bytes, bytes):
            raise TypeError("ImageProcessor expects image bytes")

        if not image_bytes:
            raise ImageProcessingError("Image data cannot be empty")

        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image.verify()

            with Image.open(BytesIO(image_bytes)) as image:
                return image.copy()

        except (UnidentifiedImageError, OSError) as exc:
            raise ImageProcessingError(
                "Image data is invalid or unsupported"
            ) from exc

    def prepare(self, image: Image.Image) -> Image.Image:
        """
        Prepare a validated image for downstream OCR/Vision processing.

        Preparation is deterministic and does not interpret image content.
        """
        if not isinstance(image, Image.Image):
            raise TypeError("ImageProcessor expects a Pillow Image")

        prepared = ImageOps.exif_transpose(image)

        if prepared.mode not in {"RGB", "RGBA"}:
            prepared = prepared.convert("RGB")

        if (
            prepared.width > self.MAX_IMAGE_DIMENSION
            or prepared.height > self.MAX_IMAGE_DIMENSION
        ):
            prepared = prepared.copy()
            prepared.thumbnail(
                (
                    self.MAX_IMAGE_DIMENSION,
                    self.MAX_IMAGE_DIMENSION,
                ),
                Image.Resampling.LANCZOS,
            )

        return prepared