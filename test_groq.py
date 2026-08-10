import asyncio

from backend.configuration.settings import settings
from groq import AsyncGroq


async def main():
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    client = AsyncGroq(
        api_key=settings.GROQ_API_KEY
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Reply with exactly: "
                    "Groq Atlas test successful."
                ),
            }
        ],
    )

    print("Groq response:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())