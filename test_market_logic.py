from backend.modules.tools.market_data import MarketDataTool


def main():
    data = {
        "volume": "105473700",
        "average_volume": "134604800",
        "datetime": "2026-08-07",
        "is_market_open": False,
        "timestamp": 1786109400,
    }

    result = MarketDataTool._normalize_quote(
        symbol="NVDA",
        data=data,
    )

    print("Normalized market data:")
    print(result)

    assert result["volume_comparison"] == "below_average"
    assert result["market_status"] == "closed"
    assert result["quote_date"] == "2026-08-07"
    assert result["is_market_open"] is False

    print()
    print("All normalized market-data checks passed.")


if __name__ == "__main__":
    main()