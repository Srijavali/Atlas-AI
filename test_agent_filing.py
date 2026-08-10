import asyncio

from backend.infrastructure.llm import GroqRouter
from backend.modules.brain import AtlasAgent


async def main():
    llm = GroqRouter()

    agent = AtlasAgent(
        llm=llm,
    )

    response = await agent.filing_query(
        text="Summarize NVIDIA's latest quarterly filing.",
        user_context={
            "interests": [
                "AI",
                "Semiconductors",
                "Generative AI",
            ],
            "tracked_entities": [
                "NVDA",
                "AMD",
                "MSFT",
            ],
        },
    )

    print("\nAtlas filing response:\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())