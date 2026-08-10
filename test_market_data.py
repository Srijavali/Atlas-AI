import asyncio

from backend.modules.tools.market_data import MarketDataTool


async def main():
    tool = MarketDataTool()

    data = await tool.get_quote("NVDA")

    print("\nMarket data:\n")

    for key, value in data.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())