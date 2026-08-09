
from io import BytesIO

import fitz
from docx import Document

from backend.domain.models.preprocessing import (
    InputType,
    PreprocessedInput,
)
from backend.modules.preprocessing.documents.document_processor import (
    DocumentProcessor,
)
from backend.modules.preprocessing.image_processor import ImageProcessor
from backend.modules.preprocessing.service import PreprocessingService
from backend.modules.preprocessing.text.normalizer import TextNormalizer


def create_pdf(text: str) -> bytes:
    document = fitz.open()

    page = document.new_page()
    page.insert_text((72, 72), text)

    content = document.tobytes()
    document.close()

    return content


def create_docx(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)

    buffer = BytesIO()
    document.save(buffer)

    return buffer.getvalue()


def create_service() -> PreprocessingService:
    return PreprocessingService(
        text_normalizer=TextNormalizer(),
        image_processor=ImageProcessor(),
        ocr_processor=None,
        vision_processor=None,
        document_processor=DocumentProcessor(),
        speech_processor=None,
    )


def test_service_processes_real_text():
    service = create_service()

    result = service.process_text(
        "   Hello    Atlas AI   "
    )

    assert isinstance(result, PreprocessedInput)
    assert result.input_type == InputType.TEXT
    assert result.text == "Hello Atlas AI"


def test_service_processes_real_txt_document():
    service = create_service()

    result = service.process_document(
        b"Hello from a real TXT document",
        filename="test.txt",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.input_type == InputType.DOCUMENT
    assert result.text == "Hello from a real TXT document"


def test_service_processes_real_pdf_document():
    service = create_service()

    result = service.process_document(
        create_pdf("Hello from a real PDF"),
        filename="test.pdf",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.input_type == InputType.DOCUMENT
    assert "Hello from a real PDF" in result.text


def test_service_processes_real_docx_document():
    service = create_service()

    result = service.process_document(
        create_docx("Hello from a real DOCX"),
        filename="test.docx",
    )

    assert isinstance(result, PreprocessedInput)
    assert result.input_type == InputType.DOCUMENT
    assert "Hello from a real DOCX" in result.text

