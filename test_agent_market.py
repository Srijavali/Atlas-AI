import asyncio

from backend.infrastructure.llm import GroqRouter
from backend.modules.brain import AtlasAgent
from backend.modules.tools.market_data import MarketDataTool


async def main():
    llm = GroqRouter()

    market_data = MarketDataTool()

    agent = AtlasAgent(
        llm=llm,
        market_data=market_data,
    )

    response = await agent.market_query(
        text="What is happening with NVIDIA's stock today?",
        user_context={
            "role": "Investor",
            "interests": [
                "Artificial Intelligence",
                "Semiconductors",
            ],
            "tracked_entities": [
                "NVDA",
                "AMD",
                "MSFT",
            ],
        },
    )

    print("\nAtlas market response:\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())