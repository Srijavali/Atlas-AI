from backend.modules.preprocessing.documents.document_processor import (
    DocumentProcessor,
)


def main():
    processor = DocumentProcessor()

    content = b"""
    Atlas AI Financial Report

    Revenue: $81.6 billion
    Net Income: $58.3 billion
    Diluted EPS: $2.39

    This document contains financial information
    for testing document preprocessing.
    """

    result = processor.process(
        content,
        filename="financial_report.txt",
    )

    print("Document preprocessing result:")
    print()
    print("Input type:", result.input_type)
    print("Text:")
    print(result.text)
    print("Metadata:")
    print(result.metadata)


if __name__ == "__main__":
    main()