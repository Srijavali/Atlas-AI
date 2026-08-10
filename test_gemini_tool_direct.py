import asyncio

from backend.infrastructure.llm.client import GeminiClient
from backend.configuration.settings import settings
from backend.modules.tools.market_data import MarketDataTool


market_data = MarketDataTool()


def get_market_quote(symbol: str) -> dict:
    """
    Get the current market quote for a stock or ETF.

    Args:
        symbol: Stock ticker such as NVDA, AMD, MSFT, or AAPL.

    Returns:
        Current normalized market data.
    """
    return asyncio.run(
        market_data.get_quote(symbol)
    )


async def main():
    keys = [
        key.strip()
        for key in settings.GEMINI_API_KEYS.split(",")
        if key.strip()
    ]

    print("Keys:", len(keys))

    client = GeminiClient(
        api_key=keys[0],
        model=settings.GEMINI_MODEL,
    )

    result = await client.generate_with_tool(
        prompt=(
            "What is the current price of NVIDIA? "
            "Use the market data tool. "
            "Do not guess the price."
        ),
        tool=get_market_quote,
    )

    print("\nResult:\n")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())