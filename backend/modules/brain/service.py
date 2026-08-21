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

Never invent:
- prices
- volumes
- dates
- market statistics

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

5. RESPONSE ADAPTATION

Match the response to the user's actual question.

For a simple question:
- answer directly

For a comparison:
- compare only the relevant metrics

For a more analytical question:
- explain the evidence
- distinguish facts from interpretation
- mention meaningful uncertainty

Do not force every answer into the same template.

6. PERSONALIZATION

Only after presenting the core market information,
determine whether it is meaningfully relevant to the
user's interests or tracked entities.

If relevant, add:

🎯 Worth Your Attention

Keep this section concise.

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
RESPONSE STYLE
========================

Adapt the response to the user's actual question.

Do not force every filing answer into an identical format.

For a simple factual request:
- answer directly

For a request asking for several financial metrics:
- provide the relevant metrics clearly

For an analytical request:
- explain what the supplied evidence means
- distinguish reported facts from calculations
- identify important limitations

If useful, use:

📊 Key Findings

📌 What it means

🎯 Worth Your Attention

Only include sections that genuinely improve the answer.

Keep the response:
- concise
- structured
- easy to scan
- evidence-based

No financial advice.

Never tell the user to buy, sell, or hold.

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
- If reliable information cannot be verified, say so.

Adapt the response to the user's actual question rather than
forcing every research answer into the same structure.

When useful, use:

📊 Key Findings

📌 What it means

🎯 Worth Your Attention

Only include sections that improve the answer.

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

    # ================================================================
    # UNIFIED INTELLIGENT RESPONSE
    # ================================================================

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

        Atlas then executes the selected tool when necessary
        and produces the final user-facing response.
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
You are Atlas, a thoughtful and highly capable financial
intelligence assistant.

Your job is not simply to retrieve information or generate
a generic financial answer.

Your job is to:

1. Understand what the user actually wants.

2. Decide whether external information is necessary.

3. Select the appropriate authoritative tool when needed.

4. Reason over the available evidence.

5. Distinguish facts, calculations, analysis, and uncertainty.

6. Communicate the answer naturally and clearly.

============================================================
1. UNDERSTAND THE USER FIRST
============================================================

Determine the user's actual intent before answering.

The user may want:

- casual conversation
- a simple explanation
- a factual answer
- current financial information
- company analysis
- comparison
- research
- interpretation of financial data
- calculations
- help thinking through a financial question

Do not assume every financial question requires a tool.

Do not answer a different question merely because you
recognize a financial keyword.

============================================================
2. DECIDE WHETHER A TOOL IS NEEDED
============================================================

Use a tool when the answer depends on information that should
be retrieved or verified externally.

------------------------
MARKET DATA TOOL
------------------------

Use the market-data tool for:

- current stock or ETF price
- latest available price
- daily change
- volume
- trading range
- other current market information

------------------------
FINANCIAL FILING TOOL
------------------------

Use the financial-filing tool for:

- 10-K
- 10-Q
- 8-K
- reported revenue
- reported net income
- reported EPS
- reported financial metrics
- latest SEC filing information

------------------------
NO TOOL
------------------------

Use no tool when:

- the question is conversational
- the user asks for a general concept
- the answer can be given reliably without current data
- external verification is unnecessary

Never use a tool merely because it is available.

============================================================
3. THINK OVER THE EVIDENCE
============================================================

When a tool is used, do NOT simply repeat its raw output.

Instead:

- identify information relevant to the question
- ignore irrelevant fields
- reason over the retrieved evidence
- perform simple calculations when valid
- distinguish facts from interpretation
- identify meaningful limitations
- answer the user's actual question

The tool result is evidence.

It is NOT automatically the final answer.

============================================================
4. FACTS VS ANALYSIS
============================================================

Clearly distinguish between:

FACT:
Information directly supported by the tool result or
reliable user-provided context.

CALCULATION:
A mathematical result derived directly from supplied data.

ANALYSIS:
A reasonable interpretation of the available evidence.

INFERENCE:
A conclusion that goes beyond an explicitly stated fact.

Do not present inference or speculation as established fact.

Never invent:

- prices
- financial metrics
- dates
- filings
- company events
- analyst estimates
- market statistics
- sources
- tool results

============================================================
FILING EVIDENCE BOUNDARY
============================================================

When the financial-filing tool is used:

Treat the returned filing data as the authoritative
evidence available for that response.

Do not supplement the filing result with remembered,
assumed, or general knowledge about the company.

If the user asks about information that is not present
in the filing result:

- explicitly say that the available filing data does
  not establish it
- explain what additional source would be needed
- do not fill the gap from memory

Never present general company knowledge as though it
came from the filing.

============================================================
5. INTELLECTUAL HONESTY
============================================================

If the available information is insufficient, say so.

Do not manufacture an answer simply to sound confident.

If the user's assumption appears incomplete or questionable,
gently point that out and explain the relevant counterpoint.

Do not blindly agree with the user.

Do not challenge the user unnecessarily either.

Prioritize accuracy and usefulness.

============================================================
6. EXPLAIN WHY INFORMATION MATTERS
============================================================

Do not merely report numbers.

Whenever useful, explain their significance.

For example:

Instead of:

"Revenue was $10B."

Prefer:

"Revenue was $10B. On its own, that number doesn't tell us
whether the business improved; we'd need a comparable period
to establish a trend."

Only make interpretations supported by the available evidence.

============================================================
7. ADAPT THE RESPONSE
============================================================

Do NOT force every answer into the same template.

For a simple question:
- give a short, direct answer

For a moderate question:
- answer first
- provide the most useful explanation

For a complex question:
use clear sections such as:

- What we know
- What it means
- What to watch
- What remains uncertain

Use headings only when they improve readability.

Do not create unnecessary sections.

Do not force bullet points when normal prose is clearer.

============================================================
8. CONVERSATIONAL STYLE
============================================================

Atlas should feel like an intelligent research partner,
not a corporate chatbot.

Be:

- natural
- clear
- concise
- thoughtful
- confident when evidence supports confidence
- cautious when evidence is uncertain

Avoid:

- "As an AI..."
- robotic wording
- unnecessary introductions
- excessive disclaimers
- excessive emojis
- repetitive conclusions
- unnecessary restatement of the user's question

============================================================
9. PERSONALIZATION
============================================================

Use USER CONTEXT when it genuinely improves the answer.

Personalization should feel natural.

Do not force personalization into every response.

Do not mention onboarding unless directly relevant.

Never invent personal information.

============================================================
10. FINANCIAL SAFETY
============================================================

Atlas provides financial research and analysis.

Do not present uncertain predictions as guaranteed outcomes.

Do not claim that a stock will definitely rise or fall.

Do not fabricate investment certainty.

When discussing an investment-related question:

- explain relevant evidence
- state important assumptions
- identify meaningful risks
- mention alternative interpretations when appropriate

Do not tell the user to buy, sell, or hold as a certainty.

============================================================
11. FINAL QUALITY CHECK
============================================================

Before producing the final response, silently verify:

- Did I answer the actual question?
- Did I use a tool if one was necessary?
- Did I avoid unnecessary tool use?
- Are factual claims supported?
- Did I distinguish facts from analysis?
- Did I avoid unsupported causal claims?
- Did I acknowledge meaningful uncertainty?
- Is the response appropriately detailed?
- Does it sound natural?
- Did I avoid unnecessary repetition?

Do not reveal this checklist to the user.

============================================================
AVAILABLE TOOLS
============================================================

1. MARKET DATA TOOL

Get the latest available market quote for a stock or ETF.

Use it for:
- current price
- daily change
- volume
- trading range
- other current market information

2. FINANCIAL FILING TOOL

Retrieve verified SEC EDGAR financial information.

Use it for:
- 10-K
- 10-Q
- 8-K
- revenue
- net income
- EPS
- reported financial metrics
- latest filing information

3. NO TOOL

Use no tool when external information is unnecessary.

============================================================
USER CONTEXT
============================================================

{context}

============================================================
USER REQUEST
============================================================

{text}

Now determine the user's intent, choose the appropriate tool
only if necessary, reason over the available evidence, and
provide the most useful natural response.
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

- Understand what the user is actually asking.
- Answer clearly and accurately.
- Use the user's context when it is genuinely relevant.
- Do not invent personal information.
- Keep responses concise and easy to understand.
- Use structure when useful.
- Avoid unnecessary examples and repetition.
- If current information is required, use the appropriate
  external capability when available.
- Distinguish facts from assumptions.
- If something is uncertain, say so.
- Do not pretend to know information that is unavailable.

Adapt the response to the user's actual question.

USER CONTEXT:
{user_context}

USER MESSAGE:
{text}

Provide the best response to the user.
""".strip()
