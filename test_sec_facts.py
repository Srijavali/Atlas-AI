
import asyncio
import json

from backend.modules.tools.financial_filings import (
    FinancialFilingTool,
)


async def main():
    tool = FinancialFilingTool()

    print("Testing SEC Company Facts...")

    result = await tool.get_financial_metrics(
        "NVDA",
        form="10-Q",
    )

    print("\nNormalized SEC financial metrics:")
    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    assert result["symbol"] == "NVDA"
    assert result["form"] == "10-Q"
    assert result["source"] == "SEC EDGAR XBRL"

    print("\nSEC Company Facts test passed.")


if __name__ == "__main__":
    asyncio.run(main())

