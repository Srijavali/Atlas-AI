
from __future__ import annotations

from backend.infrastructure.llm import GroqRouter
from backend.modules.tools.financial_filings import (
    FinancialFilingTool,
)
from backend.modules.tools.market_data import (
    MarketDataTool,
)


class AtlasAgent:
    """
    Atlas Agent.

    Responsible for:
    - normal conversational responses
    - current web research
    - live market intelligence
    - financial filing intelligence

    Tool execution is delegated to the appropriate Atlas tool,
    while Groq is responsible for reasoning and presentation.
    """

    def __init__(
        self,
        *,
        llm: GroqRouter,
        market_data: MarketDataTool | None = None,
        financial_filings: FinancialFilingTool | None = None,
    ) -> None:
        self._llm = llm

        self._market_data = (
            market_data
            or MarketDataTool()
        )

        self._financial_filings = (
            financial_filings
            or FinancialFilingTool()
        )

    # ================================================================
    # MARKET DATA
    # ================================================================

    async def _get_market_quote(
        self,
        symbol: str,
    ) -> dict:
        """
        Execute the market-data tool.
        """

        return await self._market_data.get_quote(
            symbol
        )

    async def market_query(
        self,
        *,
        text: str,
        user_context: dict | None = None,
    ) -> str:
        """
        Answer a market-related request using
        the live market-data tool.
        """

        if not isinstance(text, str):
            raise TypeError(
                "AtlasAgent expects text as a string"
            )

        text = text.strip()

        if not text:
            raise ValueError(
                "AtlasAgent cannot process empty text"
            )

        context = user_context or {}

        prompt = f"""
You are Atlas, a financial intelligence assistant.

You have access to a live market-data tool.

Use the tool whenever current market information
is required.

IMPORTANT RESPONSE PRINCIPLES:

1. FIDELITY
Use only the market information returned by the tool.
Never invent prices, volumes, dates, or market statistics.

2. TEMPORAL ACCURACY
Pay attention to:
- quote_date
- market_status
- is_market_open

If the returned quote is from an earlier trading session,
clearly say "Latest available snapshot" rather than
calling it today's live price.

3. COMPRESSION
Do not dump raw API data.
Keep only the numbers relevant to the user's request.

4. ANALYSIS
Explain what the numbers mean in simple financial language.
Do not make unsupported causal claims.

5. STRUCTURE
Use:
- concise heading
- 3–5 key points
- short "What it means" section

Avoid long paragraphs.

6. PERSONALIZATION
Only after presenting the core market information,
determine whether it is meaningfully relevant to the
user's interests or tracked entities.

If relevant, add:

🎯 Worth Your Attention

Keep this section to 1–3 concise points.

Do not repeatedly mention onboarding.
Do not force personalization when relevance is weak.

USER CONTEXT:
{context}

USER REQUEST:
{text}
""".strip()

        return await self._llm.generate_with_tool(
            prompt=prompt,
            tool=self._get_market_quote,
            tool_name="get_market_quote",
            tool_description=(
                "Get the latest available market quote "
                "for a stock or ETF. Use this whenever "
                "the user asks for current price, daily "
                "change, volume, trading range, or other "
                "current market information."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": (
                            "Stock ticker symbol, such as "
                            "NVDA, AMD, MSFT, or AAPL."
                        ),
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
        )

    # ================================================================
    # FINANCIAL FILINGS
    # ================================================================

    async def _get_financial_filing(
        self,
        symbol: str,
        form: str = "10-Q",
    ) -> dict:
        """
        Execute the financial filing tool.

        The tool returns verified SEC-derived financial data.
        """

        form = form.strip().upper()

        allowed_forms = {
            "10-K",
            "10-Q",
            "8-K",
        }

        if form not in allowed_forms:
            form = "10-Q"

        return await self._financial_filings.get_filing_snapshot(
            symbol,
            form=form,
        )

    async def filing_query(
        self,
        *,
        text: str,
        user_context: dict | None = None,
    ) -> str:
        """
        Answer a financial-filing-related request using
        SEC EDGAR and XBRL data.
        """

        if not isinstance(text, str):
            raise TypeError(
                "AtlasAgent expects text as a string"
            )

        text = text.strip()

        if not text:
            raise ValueError(
                "AtlasAgent cannot process empty text"
            )

        context = user_context or {}

        prompt = f"""
        You are Atlas, a financial intelligence assistant.

        You have access to VERIFIED financial information retrieved
        from SEC EDGAR and SEC XBRL.

        Your job is to transform those verified facts into a concise,
        easy-to-understand financial summary.

        ========================
        NON-NEGOTIABLE DATA RULES
        ========================

        1. FACTUAL FIDELITY

        Use ONLY information contained in the tool result.

        Never invent:
        - financial numbers
        - growth rates
        - analyst expectations
        - earnings beats/misses
        - market share
        - product demand
        - management statements
        - causes of financial performance
        - future outlook
        - investment conclusions

        2. NO UNSUPPORTED TRENDS

        A single reporting period does NOT establish growth,
        decline, acceleration, expansion, improvement, or deterioration.

        Only describe a trend if the tool explicitly provides
        multiple comparable periods or an explicit comparison.

        3. SAFE DERIVED CALCULATIONS

        You may perform simple arithmetic using supplied numbers.

        For example:
        - net income / revenue
        - differences between supplied values
        - percentages directly calculable from supplied values

        Clearly present these as calculations, not reported facts.

        4. SEPARATE FACT FROM INTERPRETATION

        Reported fact:
        "Revenue was $81.6B."

        Supported calculation:
        "Net income was approximately 71.5% of reported revenue."

        Unsupported:
        "Revenue grew strongly because AI demand increased."

        Do NOT make the third type of statement.

        5. SOURCE LIMITATION

        The tool currently provides SEC filing metadata and selected
        XBRL financial facts.

        It does NOT provide:
        - management discussion
        - risk-factor analysis
        - analyst estimates
        - market-share information
        - product demand analysis
        - reasons behind financial changes

        Therefore, do not claim conclusions requiring those sources.

        ========================
        RESPONSE STRUCTURE
        ========================

        📊 [Company] — [Filing Type]

        • Revenue
        • Net income
        • Diluted EPS
        • One or two other relevant supplied metrics

        📌 What it means

        Give 1–3 concise observations based ONLY on:
        - the supplied facts
        - simple calculations from those facts
        - explicitly reported filing metadata

        If there is insufficient information to establish a trend,
        say so briefly.

        🎯 Worth Your Attention

        Only include this section if the financial information has
        a meaningful connection to the user's interests or tracked
        entities.

        Keep it to 1–2 points.

        Personalization must connect the VERIFIED filing information
        to the user's context.

        Do not introduce new financial claims while personalizing.

        Do not say:
        "As you mentioned during onboarding."

        Do not force personalization.

        ========================
        STYLE
        ========================

        - Concise
        - Structured
        - Easy to scan
        - Maximum 5 key financial bullets
        - Maximum 3 "What it means" bullets
        - Maximum 2 personalization bullets
        - No long paragraphs
        - No unnecessary examples
        - No financial advice
        - Never tell the user to buy, sell, or hold

USER CONTEXT:
{context}

USER REQUEST:
{text}
""".strip()

        return await self._llm.generate_with_tool(
            prompt=prompt,
            tool=self._get_financial_filing,
            tool_name="get_financial_filing",
            tool_description=(
                "Retrieve a verified SEC EDGAR financial "
                "filing snapshot for a publicly traded "
                "company. Use this when the user asks "
                "about a company's 10-K, 10-Q, 8-K, reported "
                "financial metrics, or latest filing."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": (
                            "Stock ticker symbol, such as "
                            "NVDA, AMD, MSFT, or AAPL."
                        ),
                    },
                    "form": {
                        "type": "string",
                        "enum": [
                            "10-K",
                            "10-Q",
                            "8-K",
                        ],
                        "description": (
                            "SEC filing type. Use 10-Q for "
                            "quarterly results, 10-K for annual "
                            "results, and 8-K for current reports."
                        ),
                    },
                },
                "required": [
                    "symbol",
                    "form",
                ],
                "additionalProperties": False,
            },
        )

    # ================================================================
    # WEB RESEARCH
    # ================================================================

    async def research(
        self,
        *,
        text: str,
        user_context: dict | None = None,
    ) -> str:
        """
        Answer a request using current web information.
        """

        if not isinstance(text, str):
            raise TypeError(
                "AtlasAgent expects text as a string"
            )

        text = text.strip()

        if not text:
            raise ValueError(
                "AtlasAgent cannot research empty text"
            )

        context = user_context or {}

        prompt = f"""
You are Atlas, a professional financial research assistant.

Use current web information to answer the user's request.

Rules:

- Prefer recent and reliable sources.
- Distinguish verified facts from interpretation.
- Never invent financial information.
- Explain why important information matters.
- Keep the answer concise and useful.
- Present the discovered information first.
- Use a small number of clear bullet points.
- Avoid long paragraphs.
- Do not provide unnecessary examples.
- If examples are necessary, keep them finance-related.
- If reliable information cannot be verified, say so.

STRUCTURE:

📊 Key Findings
• 3–5 concise points

📌 What it means
• 1–3 concise analytical points

Only after the core findings, determine whether there is
a meaningful connection to the user's interests or
tracked entities.

If relevant:

🎯 Worth Your Attention
• 1–3 concise personalized points

Do not repeatedly mention onboarding.
Do not force personalization.

USER CONTEXT:
{context}

USER REQUEST:
{text}
""".strip()

        return await self._llm.generate(
            prompt=prompt,
        )


    async def intelligent_response(
    self,
    *,
    text: str,
    user_context: dict | None = None,
    ) -> str:
        """
        Unified Atlas reasoning entry point.

        Groq decides whether the request requires:
        - market data
        - SEC financial filings
        - no external tool

        Atlas executes the selected tool and Groq produces
        the final user-facing response.
        """

        if not isinstance(text, str):
            raise TypeError(
                "AtlasAgent expects text as a string"
            )

        text = text.strip()

        if not text:
            raise ValueError(
                "AtlasAgent cannot process empty text"
            )

        context = user_context or {}

        prompt = f"""
    You are Atlas, a proactive financial intelligence assistant.

    You have access to the following authoritative tools:

    1. MARKET DATA TOOL
    Use this when the user asks for:
    - current stock price
    - latest available price
    - daily change
    - volume
    - trading range
    - other current market information

    2. FINANCIAL FILING TOOL
    Use this when the user asks for:
    - company revenue from a filing
    - net income
    - EPS
    - 10-K
    - 10-Q
    - 8-K
    - reported financial metrics
    - latest SEC filing information

    3. NO TOOL
    If the question can be answered without
    current or externally verified financial data,
    answer normally without calling a tool.

    IMPORTANT RULES:

    - Never invent current market data.
    - Never invent SEC financial data.
    - Prefer the appropriate authoritative tool whenever
    the requested information requires it.
    - Do not use a tool unnecessarily.
    - Use the user's context only when it is genuinely relevant.
    - Do not mention internal tools or implementation details.
    - Do not repeatedly mention onboarding.
    - Keep the final answer concise and easy to scan.
    - Clearly distinguish verified facts from interpretation.
    - Never give buy, sell, or hold recommendations.

    USER CONTEXT:
    {context}

    USER REQUEST:
    {text}
    """.strip()

        return await self._llm.generate_with_tools(
            prompt=prompt,
            tools=[
                {
                    "tool": self._get_market_quote,
                    "tool_name": "get_market_quote",
                    "tool_description": (
                        "Get the latest available market quote "
                        "for a stock or ETF. Use this for current "
                        "price, daily change, volume, trading range, "
                        "or other current market information."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": (
                                    "Stock ticker symbol, such as "
                                    "NVDA, AMD, MSFT, or AAPL."
                                ),
                            }
                        },
                        "required": ["symbol"],
                        "additionalProperties": False,
                    },
                },
                {
                    "tool": self._get_financial_filing,
                    "tool_name": "get_financial_filing",
                    "tool_description": (
                        "Retrieve verified SEC EDGAR financial "
                        "filing information for a publicly traded "
                        "company. Use this for 10-K, 10-Q, 8-K, "
                        "revenue, net income, EPS, reported financial "
                        "metrics, or latest filing information."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": (
                                    "Stock ticker symbol, such as "
                                    "NVDA, AMD, MSFT, or AAPL."
                                ),
                            },
                            "form": {
                                "type": "string",
                                "enum": [
                                    "10-K",
                                    "10-Q",
                                    "8-K",
                                ],
                                "description": (
                                    "SEC filing type. Use 10-Q for "
                                    "quarterly results, 10-K for annual "
                                    "results, and 8-K for current reports."
                                ),
                            },
                        },
                        "required": [
                            "symbol",
                            "form",
                        ],
                        "additionalProperties": False,
                    },
                },
            ],
        )
    # ================================================================
    # GENERAL RESPONSE
    # ================================================================

    async def respond(
        self,
        *,
        text: str,
        user_context: dict | None = None,
    ) -> str:
        """
        Handle normal conversational requests.
        """

        if not isinstance(text, str):
            raise TypeError(
                "AtlasAgent expects text as a string"
            )

        text = text.strip()

        if not text:
            raise ValueError(
                "AtlasAgent cannot process empty text"
            )

        context = user_context or {}

        prompt = self._build_prompt(
            text=text,
            user_context=context,
        )

        return await self._llm.generate(
            prompt=prompt,
        )

    @staticmethod
    def _build_prompt(
        *,
        text: str,
        user_context: dict,
    ) -> str:
        return f"""
You are Atlas, a proactive personal AI assistant.

Your responsibilities:

- Understand what the user is asking.
- Answer clearly and accurately.
- Use the user's context when it is relevant.
- Do not invent personal information.
- Keep responses concise and easy to understand.
- Use structure and short sections when useful.
- Avoid unnecessary examples and repetition.
- If current information is required, use the
  appropriate external capability when available.

USER CONTEXT:
{user_context}

USER MESSAGE:
{text}

Provide the best response to the user.
""".strip()

