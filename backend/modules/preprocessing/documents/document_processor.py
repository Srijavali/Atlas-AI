
from io import BytesIO
from pathlib import Path

import fitz
from docx import Document

from backend.domain.models.preprocessing import (
    InputType,
    PreprocessedInput,
)


class DocumentProcessor:
    """Extract textual content from supported document formats."""

    SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}

    def process(
        self,
        content: bytes,
        *,
        filename: str,
    ) -> PreprocessedInput:
        if not isinstance(content, bytes):
            raise TypeError("DocumentProcessor expects bytes")

        if not content:
            raise ValueError("Document content cannot be empty")

        extension = Path(filename).suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document format: {extension or 'unknown'}"
            )

        if extension == ".txt":
            text = self._extract_txt(content)
        elif extension == ".pdf":
            text = self._extract_pdf(content)
        else:
            text = self._extract_docx(content)

        text = text.strip()

        if not text:
            raise ValueError("Document contains no extractable text")

        return PreprocessedInput(
            text=text,
            input_type=InputType.DOCUMENT,
            metadata={
                "filename": filename,
                "extension": extension,
            },
        )

    @staticmethod
    def _extract_txt(content: bytes) -> str:
        return content.decode("utf-8")

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            document = fitz.open(
                stream=content,
                filetype="pdf",
            )

            try:
                return "\n".join(
                    page.get_text()
                    for page in document
                )
            finally:
                document.close()

        except Exception as exc:
            raise ValueError("Invalid PDF document") from exc

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            document = Document(BytesIO(content))

            return "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

        except Exception as exc:
            raise ValueError("Invalid DOCX document") from exc
