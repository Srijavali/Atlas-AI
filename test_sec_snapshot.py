import asyncio
import json

from backend.modules.tools.financial_filings import (
    FinancialFilingTool,
)


async def main():
    tool = FinancialFilingTool()

    print("Testing compact SEC filing snapshot...")

    result = await tool.get_filing_snapshot(
        "NVDA",
        form="10-Q",
    )

    print("\nAtlas filing snapshot:")
    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    assert result["symbol"] == "NVDA"
    assert result["filing_type"] == "10-Q"
    assert result["metrics"]["revenue"] is not None
    assert result["metrics"]["net_income"] is not None
    assert result["metrics"]["diluted_eps"] is not None
    assert result["source"] == "SEC EDGAR XBRL"

    print("\nSEC filing snapshot test passed.")


if __name__ == "__main__":
    asyncio.run(main())