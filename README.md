# 🤖 Atlas AI

### Agentic Financial Intelligence Assistant

<p align="center">
  <b>Ask. Research. Reason. Understand.</b>
  <br>
  An AI-powered financial assistant that combines LLM reasoning,
  intelligent tool calling, financial data, persistent user context,
  scheduling, and Telegram interaction.
</p>

<p align="center">

<a href="https://t.me/Srijavalis_bot">
<img src="https://img.shields.io/badge/💬%20Live%20Demo-Telegram-229ED9?style=for-the-badge" />
</a>

<a href="https://github.com/Srijavali/Atlas-AI">
<img src="https://img.shields.io/badge/💻%20Source-GitHub-black?style=for-the-badge&logo=github" />
</a>

</p>

---

# 🌟 Overview

Financial information is spread across market feeds, regulatory filings,
company updates, and other sources.

The difficult part is not simply retrieving this information.

The real challenge is:

- understanding what the user is actually asking,
- deciding whether external information is required,
- selecting the correct tool,
- grounding the response in retrieved evidence,
- distinguishing facts from interpretation,
- remembering useful user preferences,
- and delivering information at the right time.

**Atlas AI** is designed to solve this problem.

Atlas is an **agentic financial intelligence assistant** that combines
LLM reasoning with external financial tools, persistent user context,
and scheduled workflows.

Instead of behaving like a simple chatbot:

```text
User → LLM → Answer


Atlas follows a more deliberate workflow:

User Request
      ↓
Understand Intent
      ↓
Determine Whether Information Is Needed
      ↓
Select Appropriate Tool
      ↓
Retrieve Evidence
      ↓
Reason Over Evidence
      ↓
Generate Grounded Response
      ↓
Return to User
🚀 Live Demo
💬 Try Atlas AI on Telegram

👉 https://t.me/Srijavalis_bot

You can ask questions such as:

What is an ETF?


What is NVIDIA's latest available stock price?


What was NVIDIA's latest reported revenue?


Explain the difference between revenue and net income.


Does a decline in a stock price necessarily mean
the company's business is getting weaker?
✨ Core Capabilities
🧠 1. Agentic Reasoning

Atlas uses an LLM as a reasoning layer rather than simply generating
responses from a fixed prompt.

For each request, Atlas determines:

                 User Question
                       │
                       ▼
                Understand Intent
                       │
                       ▼
             Is External Data Needed?
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       Market       SEC Filing   General
       Data?         Needed?    Question?
          │            │            │
          ▼            ▼            ▼
     Market Tool   Filing Tool   No Tool
          │            │            │
          └────────────┼────────────┘
                       ▼
                Gather Evidence
                       │
                       ▼
                 Reason Carefully
                       │
                       ▼
                 Final Response

A tool is not called simply because it exists.

For a general conceptual question, Atlas can answer directly.

For current market information, it can retrieve market data.

For reported financial information, it can use SEC filing data.

📈 2. Market Intelligence

Atlas can use a market-data capability when the user asks for
information that changes over time.

Examples:

What's NVIDIA's latest available price?


How much did NVIDIA move today?


What's the current trading volume?


What was the previous close?

The agent can work with information such as:

Current/latest available price
Daily price change
Previous close
Trading range
Volume
Market timing information

Atlas is instructed not to invent market information.

It should use the values returned by the market-data tool rather than
guessing or relying on stale model knowledge.

📑 3. SEC Financial Intelligence

Atlas can retrieve financial information from SEC EDGAR/XBRL data.

Supported filing categories include:

10-K
10-Q
8-K

Example questions:

What was NVIDIA's latest reported revenue?


What was NVIDIA's latest net income?


What did NVIDIA report in its latest 10-Q?

The filing workflow can provide reported metrics such as:

Metric	Description
Revenue	Reported company revenue
Net Income	Reported net income
EPS	Reported earnings per share
Total Assets	Reported assets
Cash	Reported cash balance
🔐 Financial Evidence & Grounding

Financial applications require a higher standard of factual reliability.

A language model can produce a convincing answer even when the underlying
information is unavailable.

Atlas therefore follows an explicit evidence-boundary principle.

When a financial tool returns information, Atlas should distinguish:

FACT

Information directly supported by retrieved data.

CALCULATION

A mathematical result derived from the available values.

ANALYSIS

An interpretation based on the available evidence.

INFERENCE

A conclusion that goes beyond directly reported information.

For example, if a filing tool only returns selected XBRL metrics, Atlas
should not automatically claim:

Revenue increased because demand for AI products increased.

unless the retrieved evidence actually establishes that.

Atlas should instead acknowledge the limitation and explain what
additional information would be required.

🎯 4. Adaptive Response Design

Atlas does not force every question into the same large response format.

Simple question
User:
What is an ETF?


Atlas:
A short and simple explanation.
Factual question
User:
What was NVIDIA's latest reported revenue?


Atlas:
Retrieves the relevant filing data
and reports the requested value.
Analytical question
User:
NVIDIA's stock has fallen recently.
Does that mean the company is getting weaker?


Atlas:
Separates stock performance from business performance
and explains what evidence should be examined.

This makes Atlas useful for both casual users and deeper financial
research workflows.

👤 Personalized Onboarding

Atlas is designed to remember useful user preferences rather than
treating every interaction as completely independent.

When a new user starts Atlas, the assistant begins a friendly onboarding
conversation.

The goal is not to collect every possible piece of information.

Instead, Atlas asks for information that can meaningfully improve
future interactions.

🌱 First Interaction Flow

The onboarding process follows a persistent state-machine architecture.

                    New User
                       │
                       ▼
              ┌─────────────────┐
              │   👋 Welcome     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Ask Name      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Ask Interests   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Ask Watchlist   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────────┐
              │ Daily Briefing?     │
              └──────────┬──────────┘
                         │
                  ┌──────┴──────┐
                  │             │
                 YES            NO
                  │             │
                  ▼             │
        ┌─────────────────┐     │
        │ Choose Time     │     │
        └────────┬────────┘     │
                 │              │
                 ▼              │
        ┌─────────────────┐     │
        │ Choose Timezone │     │
        └────────┬────────┘     │
                 │              │
                 └──────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │   Confirm     │
                └───────┬───────┘
                        │
                        ▼
                 🎉 Atlas Ready

The onboarding state is persisted so that Atlas can continue from the
appropriate state rather than relying entirely on temporary conversation
memory.

👋 What Atlas Learns
Display Name
Atlas:
😊 What should I call you?


User:
Sri

The name can then be used for a more natural interaction.

🤖 Interests

Atlas can ask what areas the user is interested in.

Examples:

AI & Technology
Startups
Investing
Fintech
Banking
Economics

The user can also respond naturally:

AI startups and semiconductor companies

rather than selecting from a fixed list.

👀 Watchlist

The user can tell Atlas what they want to keep an eye on.

Examples:

NVIDIA
Microsoft
Tesla
Indian IT
Semiconductor stocks
US technology companies

These preferences can become part of the user's persistent context.

☀️ Daily Financial Briefings

During onboarding, Atlas asks:

☀️ Would you like me to prepare a daily financial briefing for you?


Yes or no?

If the user chooses Yes, Atlas asks for a preferred delivery time.

Example:

Atlas:
Perfect! ☀️


When would you like your briefing to arrive?


User:
8:00 AM

Atlas then asks for the timezone:

Atlas:
🌍 What timezone should I use?


User:
Asia/Kolkata
🗄️ Persistent Briefing Preferences

The briefing configuration can be persisted as user preferences.

Conceptually:

briefing_enabled = true
briefing_time = 08:00
timezone = Asia/Kolkata

The workflow becomes:

User Preference
      │
      ▼
PostgreSQL
      │
      ▼
Scheduler
      │
      ▼
Scheduled Execution
      │
      ▼
Generate Financial Briefing
      │
      ▼
Telegram Notification

This means the user does not have to manually request the same briefing
every morning.

📰 What Can a Briefing Contain?

A financial briefing can bring together information relevant to the
user's interests.

Possible sections include:

📈 Market Highlights

Important market movements and available market information.

🏢 Company Updates

Relevant company developments.

👀 Watchlist Updates

Information related to companies, stocks, or sectors the user follows.

💰 Financial Developments

Important financial developments that deserve attention.

The goal is to turn scattered information into a concise and useful
summary.

🔔 Briefings vs Alerts vs Reminders

Atlas treats scheduled workflows differently depending on the user's
intent.

Workflow	Example	Purpose
☀️ Daily Briefing	"Send my briefing every morning at 8 AM."	Recurring summary
🔔 Alert	"Tell me about important updates."	Event-oriented notification
⏱️ Reminder	"Notify me about this in two minutes."	One-time notification
☀️ Daily Briefing Workflow

A daily briefing is a recurring scheduled workflow.

Example:

Send me my financial briefing every morning at 8 AM.

Conceptually:

Every Day
    │
    ▼
08:00 AM
    │
    ▼
Collect Relevant Information
    │
    ▼
Generate Briefing
    │
    ▼
Send to Telegram
🔔 Financial Alerts

Alerts are different from daily summaries.

An alert is intended to bring an important event to the user's attention.

Potential alert categories include:

Earnings announcements
Major company news
SEC filings
Large market movements
Watchlist updates
Funding events
Acquisition events

Conceptually:

Event / Monitoring
       │
       ▼
Does it match the user's preference?
       │
      YES
       │
       ▼
Generate Notification
       │
       ▼
Telegram

This moves Atlas toward a more proactive assistant experience.

⏱️ Timed Notifications

Atlas also includes scheduling and background-service infrastructure
for notification workflows.

A natural request can be expressed like:

Notify me about this in two minutes.

The intended workflow is:

User Request
     │
     ▼
Understand Intent
     │
     ▼
Extract:
 ├── What should be notified?
 └── When should it happen?
     │
     ▼
Create Scheduled Task
     │
     ▼
Wait Until Requested Time
     │
     ▼
Execute Notification
     │
     ▼
📱 Telegram

This is different from a daily briefing because it is a
one-time relative schedule rather than a recurring schedule.

🧩 Example: Complete User Journey

Imagine a new user starts Atlas.

Step 1 — Start
User:
Hi

Atlas starts onboarding.

👋 Hey! I'm Atlas.


Think of me as your personal financial research buddy.
Step 2 — Name
Atlas:
😊 What should I call you?


User:
Sri
Step 3 — Interests
Atlas:
What kind of things are you curious about?


User:
AI, semiconductors and technology
Step 4 — Watchlist
Atlas:
Is there anything you'd like me to keep an eye on?


User:
NVIDIA, Microsoft and semiconductor stocks
Step 5 — Daily Briefing
Atlas:
☀️ Would you like me to prepare a daily financial briefing?


User:
Yes

Atlas asks:

When would you like your briefing to arrive?


User:
8:00 AM

Then:

What timezone should I use?


User:
Asia/Kolkata
Step 6 — Persistence

The user's configuration is persisted:

User
 │
 ├── Name
 ├── Interests
 ├── Watchlist
 ├── Briefing Enabled
 ├── Briefing Time
 └── Timezone
       │
       ▼
   PostgreSQL
Step 7 — Proactive Interaction

At the configured time:

08:00 AM
     │
     ▼
Atlas Scheduler
     │
     ▼
Collect Relevant Data
     │
     ▼
Generate Briefing
     │
     ▼
Telegram
     │
     ▼
📱 User receives briefing

The assistant has moved from:

"Ask me something and I'll answer."

to:

"I understand what matters to you
and can proactively deliver useful information."
🧠 Persistent State Management

The onboarding process is implemented as a state-driven workflow.

Conceptually:

WELCOME
   ↓
ASK_NAME
   ↓
ASK_INTERESTS
   ↓
ASK_WATCHLIST
   ↓
ASK_DAILY_BRIEFING
   ↓
ASK_BRIEFING_TIME
   ↓
ASK_TIMEZONE
   ↓
CONFIRM
   ↓
COMPLETED

Each state determines:

What information is expected
How the response is interpreted
What information is stored
Which state comes next

This is more reliable than trying to infer the entire onboarding state
from conversation history.

🏗️ System Architecture
                         ┌─────────────────────┐
                         │    Telegram User    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │   Application API   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Atlas Agent     │
                         │ Intent + Reasoning  │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
             ┌────────────┐  ┌────────────┐  ┌────────────┐
             │   Market   │  │    SEC     │  │    No      │
             │    Tool    │  │  Filing    │  │   Tool     │
             │            │  │    Tool    │  │            │
             └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                   │               │               │
                   └───────────────┼───────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │      Groq LLM       │
                         │ Reason + Interpret  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Natural User-Facing │
                         │      Response       │
                         └─────────────────────┘


                         ┌─────────────────────┐
                         │     PostgreSQL      │
                         │ Users / Preferences │
                         │ Onboarding / State  │
                         └─────────────────────┘


                         ┌─────────────────────┐
                         │ Scheduler / Worker  │
                         │ Briefings / Tasks   │
                         └─────────────────────┘
🔄 Complete Agent Flow
                     User
                      │
                      ▼
                Telegram Bot
                      │
                      ▼
                FastAPI Backend
                      │
                      ▼
                 Atlas Agent
                      │
                      ▼
               Understand Intent
                      │
             ┌────────┼────────┐
             │        │        │
             ▼        ▼        ▼
          Market     SEC      General
           Data     Filing    Question
             │        │        │
             └────────┼────────┘
                      ▼
                Retrieve Data
                      │
                      ▼
              Evidence Boundary
                      │
                      ▼
               Groq Reasoning
                      │
                      ▼
             Natural Response
                      │
                      ▼
                  Telegram
⏰ Scheduling Architecture

Scheduled workflows operate alongside the conversational agent.

                       Atlas Application
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
       Conversational Agent             Scheduler
              │                               │
              │                        Background Worker
              │                               │
              │                    ┌──────────┴──────────┐
              │                    │                     │
              ▼                    ▼                     ▼
        User Questions        Daily Briefing        Notifications
              │                    │                     │
              └────────────────────┼─────────────────────┘
                                   ▼
                              Telegram

This separation allows scheduled tasks to operate independently from
the immediate conversational request.

🗄️ Why Persistence Matters

Without persistence:

User
 ↓
Conversation
 ↓
Application Restart
 ↓
Preferences Lost ❌

With persistence:

User
 ↓
Conversation
 ↓
PostgreSQL
 ↓
Application Restart
 ↓
Preferences Restored
 ↓
Atlas Retains Context ✅

This is especially important for a personalized assistant.

🛠️ Technology Stack
Layer	Technologies
Language	Python 3.11+
Backend	FastAPI, Uvicorn
LLM / AI	Groq, Google Gemini, OpenAI integration
Agent Architecture	LLM reasoning, Tool Calling, Prompt Engineering
Financial Data	SEC EDGAR / XBRL, Market Data API
Database	PostgreSQL
ORM	SQLAlchemy
Async Database	asyncpg
Migrations	Alembic
Messaging	Telegram Bot API
Documents	PyMuPDF, python-docx, Pillow
Configuration	Pydantic Settings, python-dotenv
Testing	Pytest, pytest-asyncio
Infrastructure	Docker Compose
Deployment	Render
Version Control	Git, GitHub
📁 Project Structure
Atlas-AI/
│
├── backend/
│   │
│   ├── app/
│   │   └── main.py
│   │
│   ├── configuration/
│   │
│   ├── infrastructure/
│   │   └── LLM / external infrastructure
│   │
│   ├── modules/
│   │   │
│   │   ├── brain/
│   │   │   └── service.py
│   │   │
│   │   ├── onboarding/
│   │   │
│   │   ├── preferences/
│   │   │
│   │   ├── scheduler/
│   │   │
│   │   └── tools/
│   │
│   ├── persistence/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── migrations/
│   │
│   └── tests/
│
├── scripts/
│
├── test_agent_filing.py
├── test_agent_market.py
├── test_agent_search.py
├── test_agent_intelligent.py
│
├── docker-compose.yml
├── render.yaml
├── alembic.ini
├── pyproject.toml
├── .env.example
└── README.md
🧪 Testing

Atlas includes automated backend tests as well as focused agent
validation scripts.

Run the complete test suite:

python -m pytest -q

Focused agent tests include:

python test_agent_market.py
python test_agent_filing.py
python test_agent_search.py
python test_agent_intelligent.py

Testing focuses on more than simply checking whether the application
starts.

Important behaviors include:

Correct tool selection
Avoiding unnecessary tools
Market-data grounding
Filing-data grounding
Response quality
Evidence boundaries
Onboarding state transitions
Preference persistence
Database persistence
Async backend behavior
🐳 Local Development
1. Clone
git clone https://github.com/Srijavali/Atlas-AI.git


cd Atlas-AI
2. Create Virtual Environment
Windows
python -m venv .venv


.\.venv\Scripts\Activate.ps1
Linux / macOS
python3 -m venv .venv


source .venv/bin/activate
3. Install Dependencies
pip install .

For development:

pip install -e ".[dev]"
4. Start PostgreSQL

Atlas includes Docker Compose configuration for local PostgreSQL.

docker compose up -d

The local PostgreSQL container is exposed on port 5433 to avoid
conflicting with an existing PostgreSQL service using the default
5432 port.

5. Configure Environment

Create:

.env

using:

.env.example

as the reference.

Required configuration includes the appropriate:

Database URL
Telegram bot token
Groq API key
Market-data API key
SEC user-agent configuration
Webhook configuration
Other model credentials where required

⚠️ Never commit .env, API keys, bot tokens, or secrets to GitHub.

6. Run Database Migrations
alembic upgrade head
7. Start the Backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

Health endpoint:

GET /health

Expected response:

{
  "status": "ok",
  "service": "atlas-ai",
  "scheduler": "running",
  "background_worker": "running",
  "telegram": "configured"
}
☁️ Deployment

Atlas is designed for deployment using Render.

The production architecture consists of:

                    GitHub
                       │
                       ▼
                    Render
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
        Atlas FastAPI      PostgreSQL
           Service           Database
              │
              ▼
          Telegram
             Bot

The deployment configuration includes:

Python application runtime
PostgreSQL database
Database migrations
FastAPI application
Health-check endpoint
Telegram integration
Environment-based secret configuration
🔐 Security & Reliability Principles

Atlas is designed with several reliability principles.

Never expose secrets

API keys and tokens are stored through environment configuration.

Never invent financial values

Market and filing values should come from the relevant tools.

Never pretend unavailable data exists

When evidence is insufficient, Atlas should communicate the limitation.

Distinguish facts from analysis

A useful interpretation should not be presented as a directly reported
fact.

Use tools selectively

External tools should only be used when the user's request actually
requires them.

💡 Engineering Challenges
1. Building an Agent Instead of a Chatbot

The first challenge was making Atlas do more than generate fluent text.

The system needed to determine:

Do I already have enough information?
          OR
Do I need external evidence?

This required designing an agentic workflow around tool selection and
evidence retrieval.

2. Financial Hallucination

Financial applications require strong grounding.

A model might confidently produce:

Revenue increased because AI demand grew.

even when the available data does not establish that.

Atlas therefore uses explicit evidence-boundary rules.

If the available filing contains only selected financial metrics,
Atlas should not invent management explanations or future guidance.

3. Designing Persistent Onboarding

The onboarding flow initially collected too much information.

The system was redesigned around the idea that the first interaction
should feel natural and lightweight.

The resulting flow focuses on information that is genuinely useful:

Name
 ↓
Interests
 ↓
Watchlist
 ↓
Briefing Preference
 ↓
Time
 ↓
Timezone

This required changes to the onboarding state machine, persistence
layer, and automated tests.

4. Response Quality

Another challenge was preventing every response from becoming a large
financial report.

Atlas therefore adapts its response to the complexity of the request.

Simple Question
      ↓
Simple Answer


Complex Question
      ↓
Evidence
+
Analysis
+
Assumptions
+
Limitations
5. Testing AI Behavior

Traditional software tests can verify whether functions return expected
values.

Agentic systems require another layer of evaluation.

Atlas is also tested for:

Tool selection
Tool restraint
Grounding
Uncertainty handling
Reasoning quality
Structured responses
Persistence
State transitions
🎓 Key Learnings

Building Atlas AI reinforced an important lesson:

Agentic AI is a systems engineering problem, not just a prompting problem.

A reliable AI assistant requires several components to work together:

        ┌───────────────┐
        │     Model     │
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │  Tool Design  │
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │ Data Grounding│
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │   Persistence │
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │    Testing    │
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │   Deployment  │
        └───────────────┘

The biggest takeaway was learning how to build an AI system that is not
only capable of generating good responses, but also knows when it
doesn't have enough evidence to answer confidently.

🔮 Future Improvements

Potential extensions include:

🔎 More financial research tools
📊 Richer company and sector analysis
📈 Portfolio-aware intelligence
🔔 More advanced financial monitoring
🧪 Dedicated agent evaluation datasets
📡 More real-time notification workflows
📊 Agent observability and quality metrics
🧠 More advanced multi-tool reasoning
🌍 Broader financial information sources

The architecture is intentionally modular so additional capabilities
can be introduced as independent tools rather than rewriting the
entire agent.

📌 Why Atlas?

Atlas is not intended to be just another chatbot.

The long-term idea is to create a financial assistant that can:

Understand
    ↓
Research
    ↓
Reason
    ↓
Remember
    ↓
Schedule
    ↓
Notify

The user should not have to repeatedly explain:

Who they are
What they care about
What they want to track
When they want information

Atlas is designed to gradually turn those preferences into useful,
persistent financial workflows.

👩‍💻 Author
Sri Javali Kotha

Computer Science & Engineering student focused on:

AI/ML • LLMs • Agentic AI • Computer Vision • AI Systems

Links
💻 GitHub: https://github.com/Srijavali
🤖 Atlas AI: https://t.me/Srijavalis_bot
