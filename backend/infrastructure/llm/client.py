from __future__ import annotations

import asyncio

from google import genai

from backend.infrastructure.llm.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
)


class GeminiClient:
    """
    Thin async wrapper around the Google GenAI SDK.

    This class owns one Gemini credential.
    Credential rotation is handled by GeminiRouter.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        self.api_key = api_key
        self.model = model

        try:
            self._client = genai.Client(api_key=api_key)
        except Exception as exc:
            raise LLMProviderError(
                "Failed to initialize Gemini client"
            ) from exc

    async def generate(
        self,
        *,
        prompt: str,
    ) -> str:
        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model,
                contents=prompt,
            )

        except Exception as exc:
            message = str(exc).lower()

            if (
                "429" in message
                or "rate limit" in message
                or "quota" in message
                or "resource exhausted" in message
            ):
                raise LLMRateLimitError(
                    "Gemini rate limit or quota exceeded"
                ) from exc

            raise LLMProviderError(
                "Gemini generation failed"
            ) from exc

        text = response.text

        if not text or not text.strip():
            raise LLMProviderError(
                "Gemini returned an empty response"
            )

        return text.strip()

    async def generate_with_tool(
        self,
        *,
        prompt: str,
        tool,
    ) -> str:
        """
        Generate a response with one Python tool available.

        Gemini decides whether the tool is required.
        The Google GenAI SDK handles the function-call cycle.
        """
        try:
            from google.genai import types

            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[tool],
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode="ANY",
                        )
                    ),
                ),
            )

        except Exception as exc:
            print("\n========== GEMINI TOOL ERROR ==========")
            print("Type:", type(exc).__name__)
            print("Error:", str(exc))
            print("=======================================\n")
            message = str(exc).lower()

            if (
                "429" in message
                or "rate limit" in message
                or "quota" in message
                or "resource exhausted" in message
            ):
                raise LLMRateLimitError(
                    "Gemini rate limit or quota exceeded"
                ) from exc

            raise LLMProviderError(
                "Gemini tool-enabled generation failed"
            ) from exc

        text = response.text

        if not text or not text.strip():
            raise LLMProviderError(
                "Gemini returned an empty tool-enabled response"
            )

        return text.strip()

    async def generate_with_search(
    self,
    *,
    prompt: str,
    ) -> str:
        """
        Generate a response using Gemini's Google Search grounding.

        Used when the request requires current or externally
        verifiable information.
        """
        try:
            from google.genai import types

            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            google_search=types.GoogleSearch()
                        )
                    ]
                ),
            )

        except Exception as exc:
            message = str(exc).lower()

            if (
                "429" in message
                or "rate limit" in message
                or "quota" in message
                or "resource exhausted" in message
            ):
                raise LLMRateLimitError(
                    "Gemini rate limit or quota exceeded"
                ) from exc

            raise LLMProviderError(
                "Gemini search-grounded generation failed"
            ) from exc

        text = response.text

        if not text or not text.strip():
            raise LLMProviderError(
                "Gemini returned an empty search-grounded response"
            )

        return text.strip()