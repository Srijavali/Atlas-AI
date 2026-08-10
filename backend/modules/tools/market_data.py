
from __future__ import annotations

from typing import Any

import httpx

from backend.configuration.settings import settings


class MarketDataError(RuntimeError):
    """Raised when market data cannot be retrieved."""


class MarketDataTool:
    """
    Retrieves market data from Twelve Data and normalizes it
    into an Atlas-friendly structure.

    Deterministic calculations such as volume comparison and
    market status are performed here rather than by the LLM.
    """

    BASE_URL = "https://api.twelvedata.com/quote"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._api_key = (
            api_key or settings.TWELVE_DATA_API_KEY
        )
        self._timeout = timeout

        if not self._api_key:
            raise MarketDataError(
                "Twelve Data API key is not configured"
            )

    async def get_quote(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Retrieve the latest available quote for a symbol.
        """

        if not isinstance(symbol, str):
            raise TypeError(
                "MarketDataTool expects symbol as a string"
            )

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError(
                "Market symbol cannot be empty"
            )

        print(
            f"[MARKET TOOL] LLM requested symbol: {symbol}"
        )

        params = {
            "symbol": symbol,
            "apikey": self._api_key,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout
            ) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                )

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError as exc:
            raise MarketDataError(
                "Twelve Data request failed"
            ) from exc

        if not isinstance(data, dict):
            raise MarketDataError(
                "Invalid response from Twelve Data"
            )

        if data.get("status") == "error":
            raise MarketDataError(
                data.get(
                    "message",
                    "Twelve Data returned an error",
                )
            )

        print(
            f"[MARKET TOOL] Twelve Data response: {data}"
        )

        return self._normalize_quote(
            symbol=symbol,
            data=data,
        )

    @staticmethod
    def _normalize_quote(
        *,
        symbol: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize Twelve Data output and perform deterministic
        calculations that should not be delegated to the LLM.
        """

        def number(
            key: str,
        ) -> float | None:
            value = data.get(key)

            if value in (None, ""):
                return None

            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        price = number("close")
        change = number("change")
        change_percent = number("percent_change")

        volume = number("volume")
        average_volume = number("average_volume")

        # ---------------------------------------------------------
        # Deterministic volume comparison
        # ---------------------------------------------------------

        volume_comparison: str | None = None

        if volume is not None and average_volume is not None:
            if volume > average_volume:
                volume_comparison = "above_average"
            elif volume < average_volume:
                volume_comparison = "below_average"
            else:
                volume_comparison = "around_average"

        # ---------------------------------------------------------
        # Deterministic market status
        # ---------------------------------------------------------

        is_market_open = data.get("is_market_open")

        if isinstance(is_market_open, bool):
            market_status = (
                "open"
                if is_market_open
                else "closed"
            )
        else:
            market_status = "unknown"

        # ---------------------------------------------------------
        # Quote date
        # ---------------------------------------------------------

        quote_date = data.get("datetime")

        # ---------------------------------------------------------
        # Normalized result
        # ---------------------------------------------------------

        return {
            "symbol": symbol,
            "name": data.get("name"),
            "exchange": data.get("exchange"),
            "currency": data.get("currency"),

            # Core quote
            "price": price,
            "change": change,
            "change_percent": change_percent,

            # Intraday information
            "open": number("open"),
            "high": number("high"),
            "low": number("low"),
            "previous_close": number(
                "previous_close"
            ),

            # Volume
            "volume": volume,
            "average_volume": average_volume,
            "volume_comparison": volume_comparison,

            # Market status / temporal information
            "quote_date": quote_date,
            "timestamp": data.get("timestamp"),
            "last_quote_at": data.get(
                "last_quote_at"
            ),
            "is_market_open": is_market_open,
            "market_status": market_status,

            # Additional provider information
            "mic_code": data.get("mic_code"),
            "fifty_two_week": data.get(
                "fifty_two_week"
            ),
        }

