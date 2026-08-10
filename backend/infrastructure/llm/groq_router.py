from __future__ import annotations

from backend.configuration.settings import settings
from backend.infrastructure.llm.exceptions import (
    LLMAllCredentialsExhaustedError,
    LLMConfigurationError,
    LLMRateLimitError,
)
from backend.infrastructure.llm.groq_client import GroqClient


class GroqRouter:
    """
    Routes Atlas requests through Groq credentials.

    Credentials are treated as primary -> standby fallbacks.
    """

    def __init__(
        self,
        *,
        api_keys: list[str] | None = None,
        model: str | None = None,
    ) -> None:

        if api_keys is None:
            api_keys = [
                settings.GROQ_API_KEY.strip()
            ] if settings.GROQ_API_KEY.strip() else []

        if not api_keys:
            raise LLMConfigurationError(
                "No Groq API keys configured"
            )

        self._api_keys = api_keys
        self._model = model or settings.GROQ_MODEL

    @property
    def credential_count(self) -> int:
        return len(self._api_keys)

    async def generate(
        self,
        *,
        prompt: str,
    ) -> str:

        errors: list[Exception] = []

        for api_key in self._api_keys:

            client = GroqClient(
                api_key=api_key,
                model=self._model,
            )

            try:
                return await client.generate(
                    prompt=prompt,
                )

            except LLMRateLimitError as exc:
                errors.append(exc)
                continue

            except Exception as exc:
                errors.append(exc)
                continue

        raise LLMAllCredentialsExhaustedError(
            f"All {len(self._api_keys)} Groq credentials failed"
        ) from errors[-1]

    async def generate_with_tool(
        self,
        *,
        prompt: str,
        tool,
        tool_name: str,
        tool_description: str,
        parameters: dict,
    ) -> str:

        errors: list[Exception] = []

        for api_key in self._api_keys:

            client = GroqClient(
                api_key=api_key,
                model=self._model,
            )

            try:
                return await client.generate_with_tool(
                    prompt=prompt,
                    tool=tool,
                    tool_name=tool_name,
                    tool_description=tool_description,
                    parameters=parameters,
                )

            except LLMRateLimitError as exc:
                errors.append(exc)
                continue

            except Exception as exc:
                errors.append(exc)
                continue

        raise LLMAllCredentialsExhaustedError(
            f"All {len(self._api_keys)} Groq credentials failed "
            "for tool-enabled generation"
        ) from errors[-1]


    async def generate_with_tools(
    self,
    *,
    prompt: str,
    tools: list[dict],
    ) -> str:
        """
        Generate a response using multiple Atlas tools.

        Credential failover remains owned by this router.
        """

        errors: list[Exception] = []

        for api_key in self._api_keys:

            client = GroqClient(
                api_key=api_key,
                model=self._model,
            )

            try:
                return await client.generate_with_tools(
                    prompt=prompt,
                    tools=tools,
                )

            except LLMRateLimitError as exc:
                errors.append(exc)
                continue

            except Exception as exc:
                errors.append(exc)
                continue

        raise LLMAllCredentialsExhaustedError(
            f"All {len(self._api_keys)} Groq credentials failed "
            "for multi-tool generation"
        ) from errors[-1]