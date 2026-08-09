import pytest

from backend.modules.preprocessing.text.normalizer import TextNormalizer


@pytest.fixture
def normalizer() -> TextNormalizer:
    return TextNormalizer()


def test_normalizer_strips_outer_whitespace(normalizer: TextNormalizer):
    result = normalizer.normalize("   Hello Atlas   ")

    assert result == "Hello Atlas"


def test_normalizer_normalizes_horizontal_whitespace(
    normalizer: TextNormalizer,
):
    result = normalizer.normalize("Hello     Atlas\tAI")

    assert result == "Hello Atlas AI"


def test_normalizer_normalizes_line_endings(
    normalizer: TextNormalizer,
):
    result = normalizer.normalize("Line one\r\nLine two\rLine three")

    assert result == "Line one\nLine two\nLine three"


def test_normalizer_preserves_paragraph_structure(
    normalizer: TextNormalizer,
):
    result = normalizer.normalize(
        "First paragraph.\n\nSecond paragraph."
    )

    assert result == "First paragraph.\n\nSecond paragraph."


def test_normalizer_limits_excessive_blank_lines(
    normalizer: TextNormalizer,
):
    result = normalizer.normalize(
        "First paragraph.\n\n\n\nSecond paragraph."
    )

    assert result == "First paragraph.\n\nSecond paragraph."


def test_normalizer_removes_invisible_artifacts(
    normalizer: TextNormalizer,
):
    result = normalizer.normalize(
        "Hel\u200blo\u2060 World\ufeff"
    )

    assert result == "Hello World"


def test_normalizer_repairs_common_encoding_issues(
    normalizer: TextNormalizer,
):
    result = normalizer.normalize("cafÃ©")

    assert result == "café"


def test_normalizer_preserves_semantic_content(
    normalizer: TextNormalizer,
):
    original = "What's Apple's stock price?"

    result = normalizer.normalize(original)

    assert result == original


def test_normalizer_rejects_non_string_input(
    normalizer: TextNormalizer,
):
    with pytest.raises(TypeError):
        normalizer.normalize(123)  # type: ignore[arg-type]


def test_normalizer_rejects_empty_text(
    normalizer: TextNormalizer,
):
    with pytest.raises(ValueError):
        normalizer.normalize("   \n\t   ")