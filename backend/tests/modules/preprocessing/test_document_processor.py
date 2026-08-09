
from io import BytesIO

import fitz
import pytest
from docx import Document

from backend.domain.models.preprocessing import InputType, PreprocessedInput
from backend.modules.preprocessing.documents.document_processor import (
    DocumentProcessor,
)


def create_pdf(text: str) -> bytes:
    document = fitz.open()

    page = document.new_page()
    page.insert_text((72, 72), text)

    pdf_bytes = document.tobytes()
    document.close()

    return pdf_bytes


def create_docx(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)

    buffer = BytesIO()
    document.save(buffer)

    return buffer.getvalue()


def test_processor_extracts_txt():
    processor = DocumentProcessor()

    result = processor.process(
        b"Hello Atlas AI",
        filename="test.txt",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.text == "Hello Atlas AI"
    assert result.input_type == InputType.DOCUMENT


def test_processor_extracts_pdf():
    processor = DocumentProcessor()

    result = processor.process(
        create_pdf("Hello from PDF"),
        filename="test.pdf",
    )

    assert isinstance(result, PreprocessedInput)
    assert "Hello from PDF" in result.text
    assert result.input_type == InputType.DOCUMENT


def test_processor_extracts_docx():
    processor = DocumentProcessor()

    result = processor.process(
        create_docx("Hello from DOCX"),
        filename="test.docx",
    )

    assert isinstance(result, PreprocessedInput)
    assert "Hello from DOCX" in result.text
    assert result.input_type == InputType.DOCUMENT


def test_processor_normalizes_outer_whitespace():
    processor = DocumentProcessor()

    result = processor.process(
        b"   Hello Atlas   ",
        filename="test.txt",
    )

    assert result.text == "Hello Atlas"


def test_processor_rejects_empty_input():
    processor = DocumentProcessor()

    with pytest.raises(ValueError):
        processor.process(
            b"",
            filename="test.txt",
        )


def test_processor_rejects_unsupported_format():
    processor = DocumentProcessor()

    with pytest.raises(ValueError):
        processor.process(
            b"some data",
            filename="test.xyz",
        )


def test_processor_rejects_invalid_pdf():
    processor = DocumentProcessor()

    with pytest.raises(ValueError):
        processor.process(
            b"not a real pdf",
            filename="broken.pdf",
        )


def test_processor_preserves_document_metadata():
    processor = DocumentProcessor()

    result = processor.process(
        b"Atlas document",
        filename="notes.txt",
    )

    assert result.metadata["filename"] == "notes.txt"

