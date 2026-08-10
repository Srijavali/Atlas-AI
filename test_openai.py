import asyncio

from backend.configuration.settings import settings
from openai import AsyncOpenAI


async def main():
    keys = [
        key.strip()
        for key in settings.OPENAI_API_KEYS.split(",")
        if key.strip()
    ]

    if not keys:
        raise RuntimeError("No OpenAI API keys configured")

    print(f"Configured OpenAI credentials: {len(keys)}")

    client = AsyncOpenAI(api_key=keys[0])

    response = await client.responses.create(
        model=settings.OPENAI_MODEL,
        input="Reply with exactly: OpenAI Atlas test successful.",
    )

    print("\nOpenAI response:")
    print(response.output_text)


if __name__ == "__main__":
    asyncio.run(main())