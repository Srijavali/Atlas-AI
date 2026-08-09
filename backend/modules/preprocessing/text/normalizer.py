import re
import unicodedata

import ftfy


# Characters that are normally accidental/invisible artifacts in user text.
# We intentionally do NOT remove all Unicode format characters because some
# are meaningful, for example Zero Width Joiner (ZWJ) in emoji sequences.
_INVISIBLE_ARTIFACTS = str.maketrans(
    {
        "\ufeff": None,  # ZERO WIDTH NO-BREAK SPACE / BOM
        "\u200b": None,  # ZERO WIDTH SPACE
        "\u2060": None,  # WORD JOINER
        "\u00ad": None,  # SOFT HYPHEN
    }
)

# Collapse horizontal whitespace without destroying meaningful newlines.
_HORIZONTAL_WHITESPACE = re.compile(r"[^\S\r\n]+")

# Preserve paragraph structure, but prevent pathological runs of blank lines.
_EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")


class TextNormalizer:
    """
    Deterministic text normalization.

    This component cleans textual representation without performing
    semantic rewriting, summarization, translation, or intent detection.
    """

    def normalize(self, text: str) -> str:
        """
        Normalize user-provided text while preserving its meaning.

        Raises:
            TypeError: If the supplied value is not a string.
            ValueError: If the normalized result is empty.
        """
        if not isinstance(text, str):
            raise TypeError("TextNormalizer expects a string")

        # Repair common encoding/mojibake issues.
        normalized = ftfy.fix_text(text)

        # Normalize Unicode compatibility representations.
        normalized = unicodedata.normalize("NFKC", normalized)

        # Normalize line endings.
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

        # Remove known invisible text artifacts.
        normalized = normalized.translate(_INVISIBLE_ARTIFACTS)

        # Normalize horizontal whitespace while preserving newlines.
        normalized = _HORIZONTAL_WHITESPACE.sub(" ", normalized)

        # Keep at most one blank line between paragraphs.
        normalized = _EXCESSIVE_NEWLINES.sub("\n\n", normalized)

        # Remove whitespace surrounding line boundaries.
        normalized = "\n".join(
            line.strip()
            for line in normalized.split("\n")
        )

        # Remove leading/trailing whitespace from the complete result.
        normalized = normalized.strip()

        if not normalized:
            raise ValueError("Normalized text cannot be empty")

        return normalized