from __future__ import annotations
import numpy as np
from dataclasses import dataclass

from PIL import Image
from paddleocr import PaddleOCR


@dataclass(slots=True)
class PaddleOCRConfig:
    """Configuration for the PaddleOCR 3.x backend."""

    text_detection_model_name: str = "PP-OCRv5_mobile_det"
    text_recognition_model_name: str = "PP-OCRv5_mobile_rec"
    lang: str = "en"

    use_doc_orientation_classify: bool = False
    use_doc_unwarping: bool = False
    use_textline_orientation: bool = False

    text_rec_score_thresh: float = 0.0


class PaddleOCRBackend:
    """
    PaddleOCR 3.x implementation of the OCR backend.

    PaddleOCR remains isolated behind this adapter so the rest of
    Atlas does not depend on PaddleOCR's API.
    """

    def __init__(
        self,
        config: PaddleOCRConfig | None = None,
    ) -> None:
        self._config = config or PaddleOCRConfig()

        self._engine = PaddleOCR(
            text_detection_model_name=(
                self._config.text_detection_model_name
            ),
            text_recognition_model_name=(
                self._config.text_recognition_model_name
            ),
            lang=self._config.lang,
            use_doc_orientation_classify=(
                self._config.use_doc_orientation_classify
            ),
            use_doc_unwarping=self._config.use_doc_unwarping,
            use_textline_orientation=(
                self._config.use_textline_orientation
            ),
        )

    def extract_text(self, image: Image.Image) -> str:
        """
        Run OCR and return recognized text in reading order.
        """

        if not isinstance(image, Image.Image):
            raise TypeError(
                "PaddleOCRBackend expects a Pillow Image"
            )

        image_array = np.array(image)

        results = self._engine.predict(image_array)

        extracted_lines: list[str] = []

        for result in results:
            result_json = result.json

            if isinstance(result_json, dict):
                data = result_json.get("res", result_json)
                rec_texts = data.get("rec_texts", [])

                for text in rec_texts:
                    if isinstance(text, str) and text.strip():
                        extracted_lines.append(text.strip())

        return "\n".join(extracted_lines).strip()