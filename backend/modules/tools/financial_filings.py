
from __future__ import annotations

from typing import Any

import httpx

from backend.configuration.settings import settings


class FinancialFilingError(RuntimeError):
    """Raised when SEC filing data cannot be retrieved."""


class FinancialFilingTool:
    """
    Retrieves public financial filing information from SEC EDGAR.

    Supported capabilities:
    - ticker -> CIK resolution
    - recent filings
    - latest filing by form
    - company XBRL facts
    - selected normalized financial metrics

    SEC public APIs do not require an API key.
    """

    COMPANY_TICKERS_URL = (
        "https://www.sec.gov/files/company_tickers.json"
    )

    SUBMISSIONS_URL = (
        "https://data.sec.gov/submissions/CIK{cik}.json"
    )

    COMPANY_FACTS_URL = (
        "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    )

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._user_agent = (
            user_agent or settings.SEC_USER_AGENT
        )
        self._timeout = timeout

        if not self._user_agent:
            raise FinancialFilingError(
                "SEC_USER_AGENT is not configured"
            )

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": self._user_agent,
            "Accept-Encoding": "gzip, deflate",
        }

    async def _get_json(
        self,
        url: str,
        *,
        host: str | None = None,
    ) -> dict[str, Any]:
        """
        Perform a GET request against a public SEC JSON endpoint.
        """

        headers = dict(self._headers)

        if host:
            headers["Host"] = host

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                headers=headers,
            ) as client:
                response = await client.get(url)

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError as exc:
            raise FinancialFilingError(
                f"SEC request failed: {url}"
            ) from exc

        if not isinstance(data, dict):
            raise FinancialFilingError(
                "SEC returned an invalid JSON response"
            )

        return data

    async def resolve_cik(
        self,
        symbol: str,
    ) -> str:
        """
        Resolve a stock ticker to its SEC CIK.
        """

        if not isinstance(symbol, str):
            raise TypeError(
                "FinancialFilingTool expects symbol as a string"
            )

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError(
                "Company symbol cannot be empty"
            )

        data = await self._get_json(
            self.COMPANY_TICKERS_URL,
        )

        for company in data.values():
            if not isinstance(company, dict):
                continue

            ticker = str(
                company.get("ticker", "")
            ).upper()

            if ticker == symbol:
                cik = company.get("cik_str")

                if cik is None:
                    break

                return str(cik).zfill(10)

        raise FinancialFilingError(
            f"SEC CIK not found for symbol: {symbol}"
        )

    async def get_recent_filings(
        self,
        symbol: str,
        *,
        forms: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Retrieve recent SEC filings for a company.
        """

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        symbol = symbol.strip().upper()

        cik = await self.resolve_cik(symbol)

        url = self.SUBMISSIONS_URL.format(
            cik=cik
        )

        data = await self._get_json(
            url,
            host="data.sec.gov",
        )

        company_name = data.get(
            "name",
            symbol,
        )

        recent = (
            data.get("filings", {})
            .get("recent", {})
        )

        if not isinstance(recent, dict):
            raise FinancialFilingError(
                "SEC recent filings data unavailable"
            )

        forms_data = recent.get(
            "form",
            [],
        )

        accession_numbers = recent.get(
            "accessionNumber",
            [],
        )

        filing_dates = recent.get(
            "filingDate",
            [],
        )

        report_dates = recent.get(
            "reportDate",
            [],
        )

        primary_documents = recent.get(
            "primaryDocument",
            [],
        )

        items: list[dict[str, Any]] = []

        for index, form in enumerate(forms_data):

            if forms and form not in forms:
                continue

            accession = (
                accession_numbers[index]
                if index < len(accession_numbers)
                else None
            )

            filing_date = (
                filing_dates[index]
                if index < len(filing_dates)
                else None
            )

            report_date = (
                report_dates[index]
                if index < len(report_dates)
                else None
            )

            primary_document = (
                primary_documents[index]
                if index < len(primary_documents)
                else None
            )

            accession_clean = (
                accession.replace("-", "")
                if isinstance(accession, str)
                else None
            )

            filing_url = None

            if (
                accession_clean
                and primary_document
            ):
                filing_url = (
                    "https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik)}/"
                    f"{accession_clean}/"
                    f"{primary_document}"
                )

            items.append(
                {
                    "form": form,
                    "filing_date": filing_date,
                    "report_date": report_date,
                    "accession_number": accession,
                    "primary_document": primary_document,
                    "filing_url": filing_url,
                }
            )

            if len(items) >= limit:
                break

        return {
            "symbol": symbol,
            "company_name": company_name,
            "cik": cik,
            "filings": items,
            "source": "SEC EDGAR",
        }

    async def get_latest_filing(
        self,
        symbol: str,
        *,
        form: str = "10-Q",
    ) -> dict[str, Any]:
        """
        Retrieve the latest filing of a specific SEC form.
        """

        result = await self.get_recent_filings(
            symbol,
            forms=[form],
            limit=1,
        )

        filings = result["filings"]

        if not filings:
            raise FinancialFilingError(
                f"No recent {form} filing found for "
                f"{symbol.upper()}"
            )

        return {
            "symbol": result["symbol"],
            "company_name": result["company_name"],
            "cik": result["cik"],
            "filing": filings[0],
            "source": "SEC EDGAR",
        }

    async def get_company_facts(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Retrieve the complete SEC Company Facts dataset
        for a company.

        This is the raw XBRL dataset from data.sec.gov.
        """

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError(
                "Company symbol cannot be empty"
            )

        cik = await self.resolve_cik(symbol)

        url = self.COMPANY_FACTS_URL.format(
            cik=cik
        )

        data = await self._get_json(
            url,
            host="data.sec.gov",
        )

        return {
            "symbol": symbol,
            "cik": cik,
            "company_name": data.get(
                "entityName",
                symbol,
            ),
            "facts": data.get(
                "facts",
                {},
            ),
            "source": "SEC EDGAR XBRL",
        }

    @staticmethod
    def _find_fact(
        *,
        facts: dict[str, Any],
        concepts: list[str],
        form: str,
        end_date: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Find the most relevant fact from candidate XBRL concepts.

        The function prefers:
        1. the requested filing form
        2. the requested reporting end date
        3. the latest filed fact
        """

        us_gaap = facts.get(
            "us-gaap",
            {},
        )

        if not isinstance(us_gaap, dict):
            return None

        candidates: list[dict[str, Any]] = []

        for concept in concepts:

            concept_data = us_gaap.get(
                concept
            )

            if not isinstance(concept_data, dict):
                continue

            units = concept_data.get(
                "units",
                {},
            )

            if not isinstance(units, dict):
                continue

            for unit_values in units.values():

                if not isinstance(
                    unit_values,
                    list,
                ):
                    continue

                for fact in unit_values:

                    if not isinstance(
                        fact,
                        dict,
                    ):
                        continue

                    if fact.get("form") != form:
                        continue

                    if (
                        end_date
                        and fact.get("end")
                        != end_date
                    ):
                        continue

                    candidates.append(
                        {
                            **fact,
                            "concept": concept,
                        }
                    )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                item.get("filed", ""),
                item.get("end", ""),
            ),
            reverse=True,
        )

        return candidates[0]

    async def get_financial_metrics(
        self,
        symbol: str,
        *,
        form: str = "10-Q",
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve a compact set of normalized financial metrics.

        Metrics:
        - revenue
        - net income
        - diluted EPS
        - total assets
        - cash and cash equivalents

        The values come directly from SEC XBRL facts.
        """

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError(
                "Company symbol cannot be empty"
            )

        latest_filing = await self.get_latest_filing(
            symbol,
            form=form,
        )

        filing = latest_filing["filing"]

        if end_date is None:
            end_date = filing.get(
                "report_date"
            )

        company_facts = await self.get_company_facts(
            symbol
        )

        facts = company_facts["facts"]

        revenue = self._find_fact(
            facts=facts,
            concepts=[
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
            ],
            form=form,
            end_date=end_date,
        )

        net_income = self._find_fact(
            facts=facts,
            concepts=[
                "NetIncomeLoss",
            ],
            form=form,
            end_date=end_date,
        )

        diluted_eps = self._find_fact(
            facts=facts,
            concepts=[
                "EarningsPerShareDiluted",
            ],
            form=form,
            end_date=end_date,
        )

        total_assets = self._find_fact(
            facts=facts,
            concepts=[
                "Assets",
            ],
            form=form,
            end_date=end_date,
        )

        cash = self._find_fact(
            facts=facts,
            concepts=[
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            ],
            form=form,
            end_date=end_date,
        )

        return {
            "symbol": symbol,
            "company_name": latest_filing[
                "company_name"
            ],
            "form": form,
            "filing_date": filing.get(
                "filing_date"
            ),
            "report_date": end_date,
            "accession_number": filing.get(
                "accession_number"
            ),
            "filing_url": filing.get(
                "filing_url"
            ),
            "metrics": {
                "revenue": revenue,
                "net_income": net_income,
                "diluted_eps": diluted_eps,
                "total_assets": total_assets,
                "cash_and_equivalents": cash,
            },
            "source": "SEC EDGAR XBRL",
        }


    async def get_filing_snapshot(
    self,
    symbol: str,
    *,
    form: str = "10-Q",
    ) -> dict[str, Any]:
        """
        Return a compact, LLM-friendly financial filing snapshot.

        Raw SEC/XBRL provenance remains available internally,
        but the LLM receives only the information needed
        for reasoning and presentation.
        """

        result = await self.get_financial_metrics(
            symbol,
            form=form,
        )

        metrics = result["metrics"]

        def format_money(
            fact: dict[str, Any] | None,
        ) -> str | None:
            if not fact:
                return None

            value = fact.get("val")

            if value is None:
                return None

            value = float(value)

            absolute = abs(value)

            if absolute >= 1_000_000_000:
                return f"${value / 1_000_000_000:.3f}B"

            if absolute >= 1_000_000:
                return f"${value / 1_000_000:.3f}M"

            if absolute >= 1_000:
                return f"${value / 1_000:.3f}K"

            return f"${value:,.2f}"

        def format_eps(
            fact: dict[str, Any] | None,
        ) -> str | None:
            if not fact:
                return None

            value = fact.get("val")

            if value is None:
                return None

            return f"${float(value):.2f}"

        return {
            "symbol": result["symbol"],
            "company": result["company_name"],
            "filing_type": result["form"],
            "filing_date": result["filing_date"],
            "period_end": result["report_date"],
            "metrics": {
                "revenue": format_money(
                    metrics.get("revenue")
                ),
                "net_income": format_money(
                    metrics.get("net_income")
                ),
                "diluted_eps": format_eps(
                    metrics.get("diluted_eps")
                ),
                "total_assets": format_money(
                    metrics.get("total_assets")
                ),
                "cash_and_equivalents": format_money(
                    metrics.get(
                        "cash_and_equivalents"
                    )
                ),
            },
            "source": result["source"],
            "filing_url": result["filing_url"],
            "accession_number": result[
                "accession_number"
            ],
        }

