from __future__ import annotations

from backend.configuration.settings import settings
from backend.infrastructure.llm.client import GeminiClient
from backend.infrastructure.llm.exceptions import (
    LLMAllCredentialsExhaustedError,
    LLMConfigurationError,
    LLMRateLimitError,
)


class GeminiRouter:
    """
    Routes Gemini requests across configured credentials.

    Each API key represents a separately configured Gemini project.

    The router does not expose API keys to the rest of Atlas.
    """

    def __init__(
        self,
        *,
        api_keys: list[str] | None = None,
        model: str | None = None,
    ) -> None:
        if api_keys is None:
            api_keys = [
                key.strip()
                for key in settings.GEMINI_API_KEYS.split(",")
                if key.strip()
            ]

        if not api_keys:
            raise LLMConfigurationError(
                "No Gemini API keys configured"
            )

        self._api_keys = api_keys
        self._model = model or settings.GEMINI_MODEL

    @property
    def credential_count(self) -> int:
        return len(self._api_keys)

    async def generate(
        self,
        *,
        prompt: str,
    ) -> str:
        errors: list[Exception] = []

        for index, api_key in enumerate(self._api_keys):
            client = GeminiClient(
                api_key=api_key,
                model=self._model,
            )

            try:
                return await client.generate(
                    prompt=prompt,
                )

            except LLMRateLimitError as exc:
                errors.append(exc)

                # Move to the next configured project/credential.
                continue

            except Exception as exc:
                errors.append(exc)

                # Provider failure on one credential should not
                # unnecessarily bring down the entire Agent.
                continue

        raise LLMAllCredentialsExhaustedError(
            f"All {len(self._api_keys)} Gemini credentials failed"
        ) from errors[-1]


    async def generate_with_tool(
        self,
        *,
        prompt: str,
        tool,
    ) -> str:
        """
        Generate a response with a custom Atlas tool.

        Credential rotation remains owned by the router.
        """

        errors: list[Exception] = []

        for api_key in self._api_keys:
            client = GeminiClient(
                api_key=api_key,
                model=self._model,
            )

            try:
                return await client.generate_with_tool(
                    prompt=prompt,
                    tool=tool,
                )

            except LLMRateLimitError as exc:
                errors.append(exc)
                continue

            except Exception as exc:
                errors.append(exc)
                continue

        raise LLMAllCredentialsExhaustedError(
            f"All {len(self._api_keys)} Gemini credentials failed "
            "for tool-enabled generation"
        ) from errors[-1]

    async def generate_with_search(
    self,
    *,
    prompt: str,
    ) -> str:
        """
        Generate a search-grounded response.

        Falls back across all configured Gemini credentials
        when a credential is rate-limited or unavailable.
        """
        errors: list[Exception] = []

        for api_key in self._api_keys:
            client = GeminiClient(
                api_key=api_key,
                model=self._model,
            )

            try:
                return await client.generate_with_search(
                    prompt=prompt,
                )

            except LLMRateLimitError as exc:
                errors.append(exc)
                continue

            except Exception as exc:
                errors.append(exc)
                continue

        raise LLMAllCredentialsExhaustedError(
            f"All {len(self._api_keys)} Gemini credentials failed "
            "for search-grounded generation"
        ) from errors[-1]