
from __future__ import annotations

import json
from typing import Any, Callable

from groq import AsyncGroq

from backend.configuration.settings import settings
from backend.infrastructure.llm.exceptions import (
    LLMProviderError,
    LLMRateLimitError,
)


class GroqClient:
    """
    Thin async wrapper around the Groq SDK.

    One GroqClient owns one API credential.
    Credential failover is handled by GroqRouter.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model or settings.GROQ_MODEL

        try:
            self._client = AsyncGroq(
                api_key=api_key
            )
        except Exception as exc:
            raise LLMProviderError(
                "Failed to initialize Groq client"
            ) from exc

    async def generate(
        self,
        *,
        prompt: str,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

        except Exception as exc:
            self._raise_provider_error(
                exc,
                "Groq generation failed",
            )

        text = response.choices[0].message.content

        if not text or not text.strip():
            raise LLMProviderError(
                "Groq returned an empty response"
            )

        return text.strip()

    async def generate_with_tool(
        self,
        *,
        prompt: str,
        tool: Callable[..., Any],
        tool_name: str,
        tool_description: str,
        parameters: dict[str, Any],
    ) -> str:
        """
        Generate a response using one local Python tool.

        Groq:

            1. Decides which arguments to pass.
            2. Returns the tool call.
            3. Atlas executes the Python tool.
            4. Atlas sends the result back to Groq.
            5. Groq generates the final user-facing response.

        This method remains available for existing
        single-tool Atlas flows.
        """

        tool_schema = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_description,
                "parameters": parameters,
            },
        }

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are Atlas, a financial intelligence assistant. "
                    "Use the provided tool when the user's request "
                    "requires information from that tool. "
                    "Never invent information that the tool can provide."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            # ---------------------------------------------------------
            # First LLM call: request the tool
            # ---------------------------------------------------------

            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[tool_schema],
                tool_choice="required",
            )

            message = response.choices[0].message

            if not message.tool_calls:
                raise LLMProviderError(
                    "Groq did not return the required tool call"
                )

            messages.append(message)

            # ---------------------------------------------------------
            # Execute every requested tool call
            # ---------------------------------------------------------

            for tool_call in message.tool_calls:

                function_name = tool_call.function.name

                if function_name != tool_name:
                    raise LLMProviderError(
                        f"Unexpected tool requested: {function_name}"
                    )

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                except json.JSONDecodeError as exc:
                    raise LLMProviderError(
                        "Groq returned invalid tool arguments"
                    ) from exc

                if not isinstance(arguments, dict):
                    raise LLMProviderError(
                        "Groq tool arguments must be a JSON object"
                    )

                try:
                    tool_result = await tool(
                        **arguments
                    )

                except TypeError as exc:
                    raise LLMProviderError(
                        "Groq supplied invalid arguments "
                        f"for tool '{tool_name}'"
                    ) from exc

                except Exception as exc:
                    raise LLMProviderError(
                        f"Atlas tool '{tool_name}' failed"
                    ) from exc

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(
                            tool_result,
                            default=str,
                        ),
                    }
                )

            # ---------------------------------------------------------
            # Second LLM call: generate final answer
            # ---------------------------------------------------------

            final_response = (
                await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
            )

        except LLMProviderError:
            raise

        except Exception as exc:
            self._raise_provider_error(
                exc,
                "Groq tool-enabled generation failed",
            )

        text = final_response.choices[0].message.content

        if not text or not text.strip():
            raise LLMProviderError(
                "Groq returned an empty tool-enabled response"
            )

        return text.strip()

    async def generate_with_tools(
        self,
        *,
        prompt: str,
        tools: list[dict[str, Any]],
    ) -> str:
        """
        Generate a response using multiple Atlas tools.

        Groq decides:

            - whether a tool is required
            - which available tool should be called
            - what arguments should be passed

        Atlas then executes the selected Python tool and
        sends the result back to Groq for the final answer.

        If Groq decides that no tool is required, the first
        response is returned directly.
        """

        if not tools:
            raise LLMProviderError(
                "At least one tool is required"
            )

        tool_schemas: list[dict[str, Any]] = []
        tool_map: dict[str, Callable[..., Any]] = {}

        # ---------------------------------------------------------
        # Validate and prepare tool definitions
        # ---------------------------------------------------------

        for tool_definition in tools:

            tool_name = tool_definition.get(
                "tool_name"
            )

            tool_description = tool_definition.get(
                "tool_description"
            )

            parameters = tool_definition.get(
                "parameters"
            )

            tool = tool_definition.get(
                "tool"
            )

            if not isinstance(
                tool_name,
                str,
            ) or not tool_name:
                raise LLMProviderError(
                    "Tool definition has an invalid tool name"
                )

            if not isinstance(
                tool_description,
                str,
            ):
                raise LLMProviderError(
                    f"Tool '{tool_name}' has an invalid "
                    "description"
                )

            if not isinstance(
                parameters,
                dict,
            ):
                raise LLMProviderError(
                    f"Tool '{tool_name}' has invalid parameters"
                )

            if not callable(tool):
                raise LLMProviderError(
                    f"Tool '{tool_name}' is not callable"
                )

            if tool_name in tool_map:
                raise LLMProviderError(
                    f"Duplicate tool name: {tool_name}"
                )

            tool_map[tool_name] = tool

            tool_schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool_description,
                        "parameters": parameters,
                    },
                }
            )

        # ---------------------------------------------------------
        # Conversation sent to Groq
        # ---------------------------------------------------------

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are Atlas, a financial intelligence "
                    "assistant. "
                    "Use an available tool whenever it provides "
                    "authoritative or current information needed "
                    "to answer the user's request. "
                    "Never invent financial data that an available "
                    "tool can provide. "
                    "If no tool is needed, answer normally."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            # -----------------------------------------------------
            # First LLM call
            #
            # Groq decides whether a tool is needed and which
            # available tool should be used.
            # -----------------------------------------------------

            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto",
            )

            message = response.choices[0].message

            # -----------------------------------------------------
            # No tool required
            # -----------------------------------------------------

            if not message.tool_calls:

                text = message.content

                if not text or not text.strip():
                    raise LLMProviderError(
                        "Groq returned an empty response"
                    )

                return text.strip()

            messages.append(message)

            # -----------------------------------------------------
            # Execute requested tool calls
            # -----------------------------------------------------

            for tool_call in message.tool_calls:

                function_name = tool_call.function.name

                tool = tool_map.get(
                    function_name
                )

                if tool is None:
                    raise LLMProviderError(
                        f"Unexpected tool requested: "
                        f"{function_name}"
                    )

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                except json.JSONDecodeError as exc:
                    raise LLMProviderError(
                        f"Groq returned invalid JSON arguments "
                        f"for tool '{function_name}'"
                    ) from exc

                if not isinstance(
                    arguments,
                    dict,
                ):
                    raise LLMProviderError(
                        f"Groq arguments for tool "
                        f"'{function_name}' must be an object"
                    )

                try:
                    tool_result = await tool(
                        **arguments
                    )

                except TypeError as exc:
                    raise LLMProviderError(
                        f"Invalid arguments supplied to "
                        f"tool '{function_name}'"
                    ) from exc

                except Exception as exc:
                    raise LLMProviderError(
                        f"Atlas tool '{function_name}' failed"
                    ) from exc

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(
                            tool_result,
                            default=str,
                        ),
                    }
                )

            # -----------------------------------------------------
            # Second LLM call
            #
            # Groq now has the actual tool result and generates
            # the final user-facing answer.
            # -----------------------------------------------------

            final_response = (
                await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
            )

        except LLMProviderError:
            raise

        except Exception as exc:
            self._raise_provider_error(
                exc,
                "Groq multi-tool generation failed",
            )

        text = final_response.choices[0].message.content

        if not text or not text.strip():
            raise LLMProviderError(
                "Groq returned an empty multi-tool response"
            )

        return text.strip()

    @staticmethod
    def _raise_provider_error(
        exc: Exception,
        default_message: str,
    ) -> None:

        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        message = str(exc).lower()

        if (
            status_code == 429
            or "rate limit" in message
            or "rate_limit" in message
            or "quota" in message
            or "too many requests" in message
        ):
            raise LLMRateLimitError(
                "Groq rate limit or quota exceeded"
            ) from exc

        raise LLMProviderError(
            default_message
        ) from exc

