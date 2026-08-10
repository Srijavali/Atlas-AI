
import asyncio

from backend.modules.tools.financial_filings import (
    FinancialFilingTool,
)


async def main():
    tool = FinancialFilingTool()

    print("Testing SEC company resolution...")

    cik = await tool.resolve_cik("NVDA")

    print("NVDA CIK:", cik)

    print("\nTesting latest 10-Q...")

    result = await tool.get_latest_filing(
        "NVDA",
        form="10-Q",
    )

    print("\nSEC Filing Result:")
    print(result)

    print("\nSEC filing test passed.")


if __name__ == "__main__":
    asyncio.run(main())

