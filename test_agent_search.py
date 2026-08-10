import asyncio

from backend.infrastructure.llm import GeminiRouter
from backend.modules.brain import AtlasAgent


async def main():
    llm = GeminiRouter()

    agent = AtlasAgent(llm=llm)

    response = await agent.research(
        text=(
            "What are the biggest market-moving events "
            "today? Focus on AI and semiconductor companies."
        ),
        user_context={
            "role": "Investor",
            "interests": [
                "AI",
                "Semiconductors",
            ],
            "tracked_entities": [
                "NVIDIA",
                "AMD",
                "Microsoft",
            ],
        },
    )

    print("\nAtlas research response:\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())