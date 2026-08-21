from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from backend.persistence.models.onboarding import SessionStatus
from backend.persistence.models.user import OnboardingStatus


@dataclass(frozen=True)
class OnboardingResult:
    step: str
    message: str
    completed: bool = False


class OnboardingService:
    """
    Deterministic + hybrid onboarding state machine for Atlas.

    The onboarding collects only the information that is most useful
    during a first interaction:
    - personalization
    - interests
    - watchlists
    - daily briefings

    Additional profile fields remain supported by the persistence layer
    and can be populated later as the user interacts with Atlas.

    Users can:
    - provide predefined or custom free-text answers
    - skip optional questions
    - configure proactive features
    """

    OPTIONAL_STEPS = {
        "ASK_ROLE",
        "ASK_MARKET_PREFERENCES",
        "ASK_WATCHLIST",
        "ASK_INSIGHT_PREFERENCES",
        "ASK_ALERTS",
        "ASK_DAILY_BRIEFING",
        "ASK_BRIEFING_TIME",
        "ASK_TIMEZONE",
    }

    # Legacy steps are kept recognized so already-started sessions can
    # be migrated safely without changing the database schema.
    LEGACY_STEP_REDIRECTS = {
        "ASK_ROLE": "ASK_INTERESTS",
        "ASK_MARKET_PREFERENCES": "ASK_WATCHLIST",
        "ASK_INSIGHT_PREFERENCES": "ASK_DAILY_BRIEFING",
        "ASK_ALERTS": "ASK_DAILY_BRIEFING",
    }

    def __init__(
        self,
        *,
        onboarding_repository,
        user_repository,
        profile_repository,
    ):
        self._onboarding_repository = onboarding_repository
        self._user_repository = user_repository
        self._profile_repository = profile_repository

    async def start(
        self,
        user_id: UUID,
    ) -> OnboardingResult:
        """
        Start onboarding or resume an existing onboarding session.
        """

        session = await self._onboarding_repository.get_by_user_id(
            user_id
        )

        if session is not None:
            # Migrate an incomplete session from the old onboarding flow.
            # Existing temporary_data is preserved; only the current step
            # is moved to the corresponding step in the shorter flow.
            if (
                session.status != SessionStatus.COMPLETED
                and session.current_step in self.LEGACY_STEP_REDIRECTS
            ):
                next_step = self.LEGACY_STEP_REDIRECTS[
                    session.current_step
                ]

                return await self._move_to_step(
                    session,
                    next_step,
                    temporary_data=self._data(session),
                )

            return OnboardingResult(
                step=session.current_step,
                message=self._message_for_step(
                    session.current_step,
                    session=session,
                ),
                completed=(
                    session.status == SessionStatus.COMPLETED
                    or session.current_step == "COMPLETED"
                ),
            )

        await self._onboarding_repository.create_session(
            user_id=user_id,
            initial_step="WELCOME",
        )

        return OnboardingResult(
            step="WELCOME",
            message=self._message_for_step("WELCOME"),
        )

    async def handle_response(
        self,
        *,
        session,
        response: str,
    ) -> OnboardingResult:
        """
        Handle one response for the current onboarding step.
        """

        current_step = session.current_step
        response = response.strip()

        # If an existing persisted session is still on a removed legacy
        # question, move it into the new flow before processing further.
        if current_step in self.LEGACY_STEP_REDIRECTS:
            next_step = self.LEGACY_STEP_REDIRECTS[current_step]

            return await self._move_to_step(
                session,
                next_step,
                temporary_data=self._data(session),
            )

        # ---------------------------------------------------------
        # WELCOME
        # ---------------------------------------------------------

        if current_step == "WELCOME":
            return await self._move_to_step(
                session,
                "ASK_NAME",
            )

        # ---------------------------------------------------------
        # NAME
        # ---------------------------------------------------------

        if current_step == "ASK_NAME":
            if not response:
                return self._retry(
                    "ASK_NAME",
                    (
                        "I didn't quite catch your name. 😊\n\n"
                        "What should I call you?\n\n"
                        "Example: Sri"
                    ),
                )

            temporary_data = self._data(session)
            temporary_data["display_name"] = response

            return await self._move_to_step(
                session,
                "ASK_INTERESTS",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # ROLE
        # ---------------------------------------------------------

        if current_step == "ASK_ROLE":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["role"] = None

                return await self._move_to_step(
                    session,
                    "ASK_INTERESTS",
                    temporary_data=temporary_data,
                )

            role = self._normalize_single_value(response)

            if not role:
                return self._retry(
                    "ASK_ROLE",
                    (
                        "No worries. 😊\n\n"
                        "What best describes you?\n\n"
                        "Examples:\n"
                        "• Student\n"
                        "• Investor\n"
                        "• Trader\n"
                        "• Analyst\n"
                        "• Founder\n"
                        "• Researcher\n\n"
                        'You can also say "skip".'
                    ),
                )

            temporary_data["role"] = role

            return await self._move_to_step(
                session,
                "ASK_INTERESTS",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # INTERESTS
        # ---------------------------------------------------------

        if current_step == "ASK_INTERESTS":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["interests"] = []

                return await self._move_to_step(
                    session,
                    "ASK_WATCHLIST",
                    temporary_data=temporary_data,
                )

            interests = self._parse_list(response)

            if not interests:
                return self._retry(
                    "ASK_INTERESTS",
                    (
                        "🎯 What topics are you interested in?\n\n"
                        "Examples:\n"
                        "• AI & technology\n"
                        "• Startups\n"
                        "• Fintech\n"
                        "• Banking\n"
                        "• Economics\n"
                        "• Investing\n\n"
                        "This helps Atlas prioritize news and "
                        "insights relevant to you.\n\n"
                        'Or say "skip".'
                    ),
                )

            temporary_data["interests"] = interests

            return await self._move_to_step(
                session,
                "ASK_WATCHLIST",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # MARKET PREFERENCES
        # ---------------------------------------------------------

        if current_step == "ASK_MARKET_PREFERENCES":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["market_preferences"] = []

                return await self._move_to_step(
                    session,
                    "ASK_WATCHLIST",
                    temporary_data=temporary_data,
                )

            market_preferences = self._parse_list(response)

            if not market_preferences:
                return self._retry(
                    "ASK_MARKET_PREFERENCES",
                    (
                        "📊 Which markets or financial areas "
                        "do you follow?\n\n"
                        "Examples:\n"
                        "• Indian stocks\n"
                        "• US stocks\n"
                        "• ETFs\n"
                        "• IPOs\n"
                        "• Crypto\n"
                        "• Banking\n"
                        "• Technology sector\n"
                        "• Global markets\n\n"
                        "This helps Atlas focus on the financial "
                        "information you actually care about.\n\n"
                        'Or say "skip".'
                    ),
                )

            temporary_data["market_preferences"] = (
                market_preferences
            )

            return await self._move_to_step(
                session,
                "ASK_WATCHLIST",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # WATCHLIST
        # ---------------------------------------------------------

        if current_step == "ASK_WATCHLIST":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["tracked_entities"] = []

                return await self._move_to_step(
                    session,
                    "ASK_DAILY_BRIEFING",
                    temporary_data=temporary_data,
                )

            tracked_entities = self._parse_list(response)

            if not tracked_entities:
                return self._retry(
                    "ASK_WATCHLIST",
                    (
                        "👀 What should Atlas keep an eye on "
                        "for you?\n\n"
                        "You can mention companies, stocks, "
                        "sectors, or markets.\n\n"
                        "Examples:\n"
                        "• NVIDIA\n"
                        "• Tesla\n"
                        "• Microsoft\n"
                        "• Reliance\n"
                        "• Indian IT sector\n"
                        "• Semiconductor companies\n\n"
                        "This helps make your research and updates "
                        "more relevant.\n\n"
                        'Nothing specific? Say "skip".'
                    ),
                )

            temporary_data["tracked_entities"] = (
                tracked_entities
            )

            return await self._move_to_step(
                session,
                "ASK_DAILY_BRIEFING",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # INSIGHT PREFERENCES
        # ---------------------------------------------------------

        if current_step == "ASK_INSIGHT_PREFERENCES":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["insight_preferences"] = []

                return await self._move_to_step(
                    session,
                    "ASK_ALERTS",
                    temporary_data=temporary_data,
                )

            preferences = self._parse_list(response)

            if not preferences:
                return self._retry(
                    "ASK_INSIGHT_PREFERENCES",
                    (
                        "📰 What kind of financial updates "
                        "matter to you?\n\n"
                        "Examples:\n"
                        "• Earnings\n"
                        "• SEC filings\n"
                        "• Company news\n"
                        "• Mergers & acquisitions\n"
                        "• Funding announcements\n"
                        "• Market-moving events\n"
                        "• Economic news\n\n"
                        "This helps Atlas understand what "
                        "deserves your attention.\n\n"
                        'Or say "skip".'
                    ),
                )

            temporary_data["insight_preferences"] = preferences

            return await self._move_to_step(
                session,
                "ASK_ALERTS",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # ALERTS
        # ---------------------------------------------------------

        if current_step == "ASK_ALERTS":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["alert_preferences"] = []

                return await self._move_to_step(
                    session,
                    "ASK_DAILY_BRIEFING",
                    temporary_data=temporary_data,
                )

            alert_preferences = self._parse_list(response)

            if not alert_preferences:
                return self._retry(
                    "ASK_ALERTS",
                    (
                        "🔔 What would you like Atlas "
                        "to alert you about?\n\n"
                        "Examples:\n"
                        "• Earnings announcements\n"
                        "• Major company news\n"
                        "• SEC filings\n"
                        "• Large market movements\n"
                        "• Watchlist updates\n"
                        "• Funding or acquisition events\n\n"
                        "This lets Atlas bring important events "
                        "to you instead of making you constantly "
                        "check for them.\n\n"
                        'Or say "skip".'
                    ),
                )

            temporary_data["alert_preferences"] = (
                alert_preferences
            )

            return await self._move_to_step(
                session,
                "ASK_DAILY_BRIEFING",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # DAILY BRIEFING
        # ---------------------------------------------------------

        if current_step == "ASK_DAILY_BRIEFING":
            normalized = response.lower()

            if self._is_skip(response):
                briefing_enabled = False

            elif normalized in {
                "yes",
                "y",
                "yeah",
                "yep",
                "sure",
                "please",
                "daily",
                "every day",
            }:
                briefing_enabled = True

            elif normalized in {
                "no",
                "n",
                "nope",
                "not now",
                "not yet",
            }:
                briefing_enabled = False

            else:
                return self._retry(
                    "ASK_DAILY_BRIEFING",
                    (
                        "☀️ Would you like a personalized "
                        "daily briefing?\n\n"
                        "It can summarize the markets, "
                        "companies, and topics you care about.\n\n"
                        "Examples:\n"
                        "• Market highlights\n"
                        "• Watchlist updates\n"
                        "• Important financial news\n"
                        "• Major developments\n\n"
                        "Reply with yes, no, or skip."
                    ),
                )

            temporary_data = self._data(session)

            temporary_data["briefing_enabled"] = (
                briefing_enabled
            )

            if not briefing_enabled:
                temporary_data["briefing_time"] = None

                return await self._move_to_step(
                    session,
                    "ASK_TIMEZONE",
                    temporary_data=temporary_data,
                )

            return await self._move_to_step(
                session,
                "ASK_BRIEFING_TIME",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # BRIEFING TIME
        # ---------------------------------------------------------

        if current_step == "ASK_BRIEFING_TIME":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["briefing_time"] = None

                return await self._move_to_step(
                    session,
                    "ASK_TIMEZONE",
                    temporary_data=temporary_data,
                )

            briefing_time = self._parse_time(response)

            if briefing_time is None:
                return self._retry(
                    "ASK_BRIEFING_TIME",
                    (
                        "⏰ What time should I send "
                        "your daily briefing?\n\n"
                        "Examples:\n"
                        "• 7:30 AM\n"
                        "• 8:00 AM\n"
                        "• 8:30 AM\n"
                        "• 9:00 AM\n"
                        "• 6:00 PM\n\n"
                        "Choose whatever fits your routine."
                    ),
                )

            temporary_data["briefing_time"] = (
                briefing_time.isoformat()
            )

            return await self._move_to_step(
                session,
                "ASK_TIMEZONE",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # TIMEZONE
        # ---------------------------------------------------------

        if current_step == "ASK_TIMEZONE":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["timezone"] = None

                return await self._move_to_step(
                    session,
                    "CONFIRM",
                    temporary_data=temporary_data,
                )

            timezone_name = self._validate_timezone(
                response
            )

            if timezone_name is None:
                return self._retry(
                    "ASK_TIMEZONE",
                    (
                        "🌍 Which timezone should Atlas use?\n\n"
                        "Examples:\n"
                        "• Asia/Kolkata\n"
                        "• America/New_York\n"
                        "• Europe/London\n"
                        "• Asia/Singapore\n"
                        "• Australia/Sydney\n\n"
                        "This makes sure your briefings and "
                        "scheduled alerts arrive at the right "
                        "local time.\n\n"
                        'You can also say "skip".'
                    ),
                )

            temporary_data["timezone"] = timezone_name

            return await self._move_to_step(
                session,
                "CONFIRM",
                temporary_data=temporary_data,
            )

        # ---------------------------------------------------------
        # CONFIRM
        # ---------------------------------------------------------

        if current_step == "CONFIRM":
            normalized = response.lower()

            if normalized in {
                "yes",
                "y",
                "yes looks good",
                "looks good",
                "correct",
                "confirm",
                "confirmed",
                "perfect",
            }:
                return await self._complete_onboarding(
                    session
                )

            if normalized in {
                "no",
                "n",
                "change",
                "edit",
                "something else",
            }:
                return OnboardingResult(
                    step="CONFIRM",
                    message=(
                        "Of course! 😊\n\n"
                        "Tell me what you'd like to change.\n\n"
                        "Examples:\n"
                        "• Change my interests\n"
                        "• Change my markets\n"
                        "• Change what I watch\n"
                        "• Change my alerts\n"
                        "• Change my briefing time\n"
                        "• Turn off my daily briefing\n\n"
                        "I'll help you update it."
                    ),
                )

            return self._retry(
                "CONFIRM",
                (
                    "Does everything look right? 😊\n\n"
                    'Say "yes" to finish, or tell me '
                    "what you'd like to change."
                ),
            )

        raise ValueError(
            f"Unknown onboarding step: {current_step}"
        )

    # ---------------------------------------------------------
    # COMPLETION
    # ---------------------------------------------------------

    async def _complete_onboarding(
        self,
        session,
    ) -> OnboardingResult:

        temporary_data = self._data(session)

        briefing_time = self._parse_stored_time(
            temporary_data.get("briefing_time")
        )

        await self._profile_repository.create_or_update_profile(
            user_id=session.user_id,
            role=temporary_data.get("role"),
            interests=temporary_data.get(
                "interests",
                [],
            ),
            market_preferences=temporary_data.get(
                "market_preferences",
                [],
            ),
            tracked_entities=temporary_data.get(
                "tracked_entities",
                [],
            ),
            insight_preferences=temporary_data.get(
                "insight_preferences",
                [],
            ),
            alert_preferences=temporary_data.get(
                "alert_preferences",
                [],
            ),
            briefing_enabled=temporary_data.get(
                "briefing_enabled",
                False,
            ),
            briefing_time=briefing_time,
            timezone_str=temporary_data.get(
                "timezone"
            ),
        )

        await self._onboarding_repository.complete_session(
            session.id
        )

        await self._user_repository.update_onboarding_status(
            user_id=session.user_id,
            status=OnboardingStatus.COMPLETED,
            display_name=temporary_data.get(
                "display_name"
            ),
        )

        return OnboardingResult(
            step="COMPLETED",
            message=self._message_for_step(
                "COMPLETED",
                session=session,
                temporary_data=temporary_data,
            ),
            completed=True,
        )

    # ---------------------------------------------------------
    # STATE TRANSITION
    # ---------------------------------------------------------

    async def _move_to_step(
        self,
        session,
        next_step: str,
        *,
        temporary_data: dict[str, Any] | None = None,
    ) -> OnboardingResult:

        await self._onboarding_repository.update_step_data(
            session_id=session.id,
            current_step=next_step,
            temporary_data=temporary_data,
        )

        return OnboardingResult(
            step=next_step,
            message=self._message_for_step(
                next_step,
                session=session,
                temporary_data=temporary_data,
            ),
        )

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _data(session) -> dict[str, Any]:
        return dict(
            session.temporary_data or {}
        )

    @staticmethod
    def _retry(
        step: str,
        message: str,
    ) -> OnboardingResult:
        return OnboardingResult(
            step=step,
            message=message,
        )

    @staticmethod
    def _is_skip(
        response: str,
    ) -> bool:
        return response.strip().lower() in {
            "skip",
            "skipping",
            "not now",
            "later",
            "none",
            "nothing",
            "no preference",
        }

    @staticmethod
    def _parse_list(
        response: str,
    ) -> list[str]:
        """
        Parse comma/newline/semicolon separated values
        while removing duplicates.
        """

        normalized = (
            response
            .replace("\n", ",")
            .replace(";", ",")
        )

        values = [
            item.strip()
            for item in normalized.split(",")
            if item.strip()
        ]

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            key = value.casefold()

            if key not in seen:
                seen.add(key)
                result.append(value)

        return result

    @staticmethod
    def _normalize_single_value(
        response: str,
    ) -> str | None:

        value = response.strip()

        if not value:
            return None

        return value

    @staticmethod
    def _parse_time(
        value: str,
    ) -> time | None:

        normalized = value.strip().lower()

        formats = (
            "%I:%M %p",
            "%I %p",
            "%H:%M",
            "%H",
        )

        from datetime import datetime

        for fmt in formats:
            try:
                parsed = datetime.strptime(
                    normalized,
                    fmt,
                )

                return parsed.time().replace(
                    second=0,
                    microsecond=0,
                )

            except ValueError:
                continue

        return None

    @staticmethod
    def _parse_stored_time(
        value: str | None,
    ) -> time | None:

        if not value:
            return None

        try:
            hours, minutes, seconds = map(
                int,
                value.split(":"),
            )

            return time(
                hour=hours,
                minute=minutes,
                second=seconds,
            )

        except (ValueError, TypeError):
            return None

    @staticmethod
    def _validate_timezone(
        value: str,
    ) -> str | None:

        timezone_name = value.strip()

        if not timezone_name:
            return None

        try:
            ZoneInfo(timezone_name)
            return timezone_name

        except Exception:
            return None

    # ---------------------------------------------------------
    # CONFIRMATION
    # ---------------------------------------------------------

    @staticmethod
    def _build_confirmation_message(
        data: dict[str, Any],
    ) -> str:

        display_name = data.get(
            "display_name"
        )

        role = data.get(
            "role"
        )

        interests = data.get(
            "interests",
            [],
        )

        markets = data.get(
            "market_preferences",
            [],
        )

        tracked = data.get(
            "tracked_entities",
            [],
        )

        insights = data.get(
            "insight_preferences",
            [],
        )

        alerts = data.get(
            "alert_preferences",
            [],
        )

        briefing_enabled = data.get(
            "briefing_enabled",
            False,
        )

        briefing_time = data.get(
            "briefing_time"
        )

        timezone = data.get(
            "timezone"
        )

        lines = [
            "✨ Almost there!",
            "",
            "Here's what I've learned about you:",
            "",
        ]

        if display_name or role:
            lines.append("👤 About you")

            if display_name and role:
                lines.append(
                    f"   {display_name} · {role}"
                )

            elif display_name:
                lines.append(
                    f"   {display_name}"
                )

            elif role:
                lines.append(
                    f"   {role}"
                )

            lines.append("")

        if interests:
            lines.extend([
                "🎯 Interests",
                f"   {', '.join(interests)}",
                "",
            ])

        if markets:
            lines.extend([
                "📊 Markets & financial areas",
                f"   {', '.join(markets)}",
                "",
            ])

        if tracked:
            lines.extend([
                "🔎 Watching",
                f"   {', '.join(tracked)}",
                "",
            ])

        if insights:
            lines.extend([
                "📰 Insights",
                f"   {', '.join(insights)}",
                "",
            ])

        if alerts:
            lines.extend([
                "🔔 Alerts",
                f"   {', '.join(alerts)}",
                "",
            ])

        if briefing_enabled:
            briefing = "Enabled"

            if briefing_time:
                briefing = (
                    f"Enabled · {briefing_time}"
                )

            lines.extend([
                "☀️ Daily briefing",
                f"   {briefing}",
                "",
            ])

        else:
            lines.extend([
                "☀️ Daily briefing",
                "   Off",
                "",
            ])

        if timezone:
            lines.extend([
                "🌏 Timezone",
                f"   {timezone}",
                "",
            ])

        lines.extend([
            "────────────────────",
            "",
            "🎯 Your Atlas profile is ready.",
            "",
            "These preferences help me personalize "
            "your research, alerts, and briefings.",
            "",
            "Does everything look right? 😊",
            "",
            'Say "yes" to finish, or tell me '
            "what you'd like to change.",
        ])

        return "\n".join(lines)

    # ---------------------------------------------------------
    # MESSAGES
    # ---------------------------------------------------------

    @staticmethod
    def _message_for_step(
        step: str,
        *,
        session=None,
        temporary_data: dict[str, Any] | None = None,
    ) -> str:

        data = temporary_data

        if data is None and session is not None:
            data = dict(
                session.temporary_data or {}
            )

        data = data or {}

        if step == "CONFIRM":
            return OnboardingService._build_confirmation_message(
                data
            )

        if step == "COMPLETED":
            return (
                 "🎉 You're all set!\n\n"
                 "Atlas is ready when you are. You can ask me about a company, "
                 "a stock, a market, an SEC filing — or just throw me a question "
                 "and let's figure it out together. 🚀"
	    )

        messages = {
            "WELCOME": (
                "👋 Hey! I'm Atlas.\n\n"
                "Think of me as your personal financial research buddy. "
                "I can help you explore companies, understand markets, "
                "dig through filings, and keep an eye on the things "
                "that matter to you.\n\n"
                "Before we get started, let me learn a little about you. "
                "Nothing complicated — just a few quick questions. 😊\n\n"
                "Let's get started!"
            ),

            "ASK_NAME": (
                "😊 What should I call you?\n\n"
                "Example: Sri"
            ),

            "ASK_ROLE": (
                "Nice to meet you! 👋\n\n"
                "What best describes you?\n\n"
                "Examples:\n"
                "• Student\n"
                "• Investor\n"
                "• Trader\n"
                "• Analyst\n"
                "• Founder\n"
                "• Researcher\n\n"
                "This helps me tailor the depth and style "
                "of information I give you.\n\n"
                'You can also say "skip".'
            ),

            "ASK_INTERESTS": (
                "Nice to meet you! 😊\n\n"
                "Now tell me — what kind of things are you curious about?\n\n"
                "You can mention anything you follow:\n\n"
                "🤖 AI & technology\n"
                "🚀 Startups\n"
                "📈 Investing\n"
                "💰 Fintech\n"
                "🏦 Banking\n"
                "🌍 Economics\n\n"
                "Or just tell me in your own words. There's no wrong answer!\n\n"
                'You can also say "skip".'
            ),

            "ASK_MARKET_PREFERENCES": (
                "📊 Which markets or financial areas "
                "do you follow?\n\n"
                "Examples:\n"
                "• Indian stocks\n"
                "• US stocks\n"
                "• ETFs\n"
                "• IPOs\n"
                "• Crypto\n"
                "• Banking\n"
                "• Technology sector\n"
                "• Global markets\n\n"
                "This helps Atlas focus on the financial "
                "information you actually care about.\n\n"
                'Or say "skip".'
            ),

            "ASK_WATCHLIST": (
                "Ooh, I like that. 👀\n\n"
                "Is there anything you'd like me to keep an eye on for you?\n\n"
                "It could be a company, stock, sector, or even a whole market.\n\n"
                "For example:\n"
                "NVIDIA, Tesla, Indian IT, semiconductor stocks\n\n"
                'Nothing specific yet? No worries — just say "skip". 😊'
            ),

            "ASK_INSIGHT_PREFERENCES": (
                "📰 What kind of financial updates "
                "matter to you?\n\n"
                "Examples:\n"
                "• Earnings\n"
                "• SEC filings\n"
                "• Company news\n"
                "• Mergers & acquisitions\n"
                "• Funding announcements\n"
                "• Market-moving events\n"
                "• Economic news\n\n"
                "This helps Atlas understand what "
                "deserves your attention.\n\n"
                'Or say "skip".'
            ),

            "ASK_ALERTS": (
                "🔔 What would you like Atlas "
                "to alert you about?\n\n"
                "Examples:\n"
                "• Earnings announcements\n"
                "• Major company news\n"
                "• SEC filings\n"
                "• Large market movements\n"
                "• Watchlist updates\n"
                "• Funding or acquisition events\n\n"
                "This lets Atlas bring important events "
                "to you instead of making you constantly "
                "check for them.\n\n"
                'Or say "skip".'
            ),

            "ASK_DAILY_BRIEFING": (
                "☀️ One more thing before I let you loose on the markets. 😄\n\n"
                "Would you like me to prepare a daily financial briefing for you?\n\n"
                "I can bring together things like:\n"
                "• Market highlights\n"
                "• Important company news\n"
                "• Updates from your watchlist\n"
                "• Major financial developments\n\n"
                "Yes or no?"
            ),

            "ASK_BRIEFING_TIME": (
                "Perfect! ☀️\n\n"
                "When would you like your briefing to arrive?\n\n"
                "For example: 8:00 AM"
            ),

            "ASK_TIMEZONE": (
                "🌍 And what timezone should I use?\n\n"
                "You can simply say something like:\n"
                "Asia/Kolkata\n\n"
                "If you're not sure, you can say \"skip\"."
            ),
        }

        try:
            return messages[step]

        except KeyError as exc:
            raise ValueError(
                f"No onboarding message defined for step: {step}"
            ) from exc