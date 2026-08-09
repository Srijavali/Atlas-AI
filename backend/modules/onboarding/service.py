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

    The state machine itself is deterministic.

    Users can:
    - choose predefined options
    - provide custom free-text answers
    - skip optional questions

    The service owns onboarding behavior and delegates persistence
    to repositories. Repositories do not commit transactions.
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
        Handle a response for the current onboarding step.
        """

        current_step = session.current_step
        response = response.strip()

        # -----------------------------------------------------
        # WELCOME
        # -----------------------------------------------------

        if current_step == "WELCOME":
            return await self._move_to_step(
                session,
                "ASK_NAME",
            )

        # -----------------------------------------------------
        # NAME
        # -----------------------------------------------------

        if current_step == "ASK_NAME":
            if not response:
                return self._retry(
                    "ASK_NAME",
                    (
                        "I didn't quite catch your name. 😊\n\n"
                        "What should I call you?"
                    ),
                )

            temporary_data = self._data(session)
            temporary_data["display_name"] = response

            return await self._move_to_step(
                session,
                "ASK_ROLE",
                temporary_data=temporary_data,
            )

        # -----------------------------------------------------
        # ROLE
        # -----------------------------------------------------

        if current_step == "ASK_ROLE":
            if self._is_skip(response):
                temporary_data = self._data(session)
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
                        "Tell me in your own words what you do, "
                        "or say \"skip\" if you'd rather skip this."
                    ),
                )

            temporary_data = self._data(session)
            temporary_data["role"] = role

            return await self._move_to_step(
                session,
                "ASK_INTERESTS",
                temporary_data=temporary_data,
            )

        # -----------------------------------------------------
        # INTERESTS
        # -----------------------------------------------------

        if current_step == "ASK_INTERESTS":
            if self._is_skip(response):
                temporary_data = self._data(session)
                temporary_data["interests"] = []

                return await self._move_to_step(
                    session,
                    "ASK_MARKET_PREFERENCES",
                    temporary_data=temporary_data,
                )

            interests = self._parse_list(response)

            if not interests:
                return self._retry(
                    "ASK_INTERESTS",
                    (
                        "Tell me at least one thing you're interested in. 😊\n\n"
                        "For example: AI, technology, startups, "
                        "stocks, or financial news.\n\n"
                        "Or say \"skip\"."
                    ),
                )

            temporary_data = self._data(session)
            temporary_data["interests"] = interests

            return await self._move_to_step(
                session,
                "ASK_MARKET_PREFERENCES",
                temporary_data=temporary_data,
            )

        # -----------------------------------------------------
        # MARKET PREFERENCES
        # -----------------------------------------------------

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
                        "Which markets or financial areas interest you? 📊\n\n"
                        "For example: Indian stocks, US stocks, ETFs, "
                        "IPOs, crypto, sectors, or the economy.\n\n"
                        "Or say \"skip\"."
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

        # -----------------------------------------------------
        # WATCHLIST / TRACKED ENTITIES
        # -----------------------------------------------------

        if current_step == "ASK_WATCHLIST":
            temporary_data = self._data(session)

            if self._is_skip(response):
                temporary_data["tracked_entities"] = []

                return await self._move_to_step(
                    session,
                    "ASK_INSIGHT_PREFERENCES",
                    temporary_data=temporary_data,
                )

            tracked_entities = self._parse_list(response)

            if not tracked_entities:
                return self._retry(
                    "ASK_WATCHLIST",
                    (
                        "You can name companies, stocks, sectors, "
                        "or markets you'd like me to watch. 🔎\n\n"
                        "For example: NVIDIA, Microsoft, "
                        "semiconductors, or Indian markets.\n\n"
                        "Or say \"skip\"."
                    ),
                )

            temporary_data["tracked_entities"] = (
                tracked_entities
            )

            return await self._move_to_step(
                session,
                "ASK_INSIGHT_PREFERENCES",
                temporary_data=temporary_data,
            )

        # -----------------------------------------------------
        # INSIGHT PREFERENCES
        # -----------------------------------------------------

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
                        "What kind of information would be most "
                        "useful to you? 📰\n\n"
                        "For example: earnings, company news, filings, "
                        "market-moving events, M&A, or macro news.\n\n"
                        "Or say \"skip\"."
                    ),
                )

            temporary_data["insight_preferences"] = preferences

            return await self._move_to_step(
                session,
                "ASK_ALERTS",
                temporary_data=temporary_data,
            )

        # -----------------------------------------------------
        # ALERTS
        # -----------------------------------------------------

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
                        "Is there anything you'd like me to watch for? 🔔\n\n"
                        "For example: earnings, company announcements, "
                        "filings, funding events, or big market moves.\n\n"
                        "Or say \"skip\"."
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

        # -----------------------------------------------------
        # DAILY BRIEFING
        # -----------------------------------------------------

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
                        "Would you like a daily briefing from Atlas? ☀️\n\n"
                        "You can say yes, no, or skip."
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

        # -----------------------------------------------------
        # BRIEFING TIME
        # -----------------------------------------------------

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
                        "I couldn't quite understand that time. 😊\n\n"
                        "Try something like 9 PM or 8:30 AM."
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

        # -----------------------------------------------------
        # TIMEZONE
        # -----------------------------------------------------

        if current_step == "ASK_TIMEZONE":
            if self._is_skip(response):
                temporary_data = self._data(session)
                temporary_data["timezone"] = None

                return await self._move_to_step(
                    session,
                    "CONFIRM",
                    temporary_data=temporary_data,
                )

            timezone_name = self._validate_timezone(response)

            if timezone_name is None:
                return self._retry(
                    "ASK_TIMEZONE",
                    (
                        "I couldn't recognize that timezone. 🌏\n\n"
                        "For example: Asia/Kolkata, "
                        "America/New_York, or Europe/London.\n\n"
                        "You can also say \"skip\"."
                    ),
                )

            temporary_data = self._data(session)
            temporary_data["timezone"] = timezone_name

            return await self._move_to_step(
                session,
                "CONFIRM",
                temporary_data=temporary_data,
            )

        # -----------------------------------------------------
        # CONFIRM
        # -----------------------------------------------------

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
                        "For example:\n"
                        "• Change my interests\n"
                        "• Change my briefing time\n"
                        "• Turn off my daily briefing\n\n"
                        "I'll help you update it."
                    ),
                )

            return self._retry(
                "CONFIRM",
                (
                    "Does everything look right? 😊\n\n"
                    "Say \"yes\" to finish, or tell me "
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
            timezone_str=temporary_data.get("timezone"),
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
        return dict(session.temporary_data or {})

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
    def _is_skip(response: str) -> bool:
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
    def _parse_list(response: str) -> list[str]:
        """
        Parse comma/newline/semicolon separated custom input.

        Examples:
            AI, startups, technology
            NVIDIA
            Microsoft
            AI; fintech; semiconductors
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
    # CONFIRMATION MESSAGE
    # ---------------------------------------------------------

    @staticmethod
    def _build_confirmation_message(
        data: dict[str, Any],
    ) -> str:

        display_name = data.get("display_name")
        role = data.get("role")
        interests = data.get("interests", [])
        markets = data.get("market_preferences", [])
        tracked = data.get("tracked_entities", [])
        insights = data.get("insight_preferences", [])
        alerts = data.get("alert_preferences", [])
        briefing_enabled = data.get(
            "briefing_enabled",
            False,
        )
        briefing_time = data.get("briefing_time")
        timezone = data.get("timezone")

        lines = [
            "✨ Almost there!",
            "",
            "Here's what I've got so far:",
            "",
        ]

        if display_name:
            lines.extend([
                f"👋 I'll call you: {display_name}",
                "",
            ])

        if role:
            lines.extend([
                f"💼 You are: {role}",
                "",
            ])

        if interests:
            lines.extend([
                f"📈 Interests: {', '.join(interests)}",
                "",
            ])

        if markets:
            lines.extend([
                f"📊 Markets: {', '.join(markets)}",
                "",
            ])

        if tracked:
            lines.extend([
                f"🔎 Watching: {', '.join(tracked)}",
                "",
            ])

        if insights:
            lines.extend([
                f"📰 Insights: {', '.join(insights)}",
                "",
            ])

        if alerts:
            lines.extend([
                f"🔔 Alerts: {', '.join(alerts)}",
                "",
            ])

        if briefing_enabled:
            briefing = "Enabled"

            if briefing_time:
                briefing = (
                    f"Enabled · {briefing_time}"
                )

            lines.extend([
                f"☀️ Daily briefing: {briefing}",
                "",
            ])
        else:
            lines.extend([
                "☀️ Daily briefing: Off",
                "",
            ])

        if timezone:
            lines.extend([
                f"🌏 Timezone: {timezone}",
                "",
            ])

        lines.extend([
            "Does everything look right?",
            "",
            'Say "yes" to finish, or tell me what '
            "you'd like to change. 😊",
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
            data = dict(session.temporary_data or {})

        data = data or {}

        if step == "CONFIRM":
            return OnboardingService._build_confirmation_message(
                data
            )

        if step == "COMPLETED":
            return (
                "You're all set! 🎉\n\n"
                "Atlas will use what you've shared to make your "
                "updates, research, alerts, and briefings more useful.\n\n"
                "And don't worry — you can change your "
                "preferences anytime.\n\n"
                "What would you like to do first?"
            )

        messages = {
            "WELCOME": (
                "Hey! 👋 I'm Atlas.\n\n"
                "I can help you keep up with markets, companies, "
                "financial news, research, and the things you care about.\n\n"
                "Let's get to know you a little first.\n\n"
                "What should I call you?"
            ),

            "ASK_NAME": (
                "What should I call you? 😊"
            ),

            "ASK_ROLE": (
                "Nice to meet you! 😊\n\n"
                "What do you do?\n\n"
                "For example: investor, analyst, founder, "
                "researcher, finance professional, or student.\n\n"
                "You can also tell me in your own words, or say "
                "\"skip\" if you'd rather skip this."
            ),

            "ASK_INTERESTS": (
                "Nice! 📈\n\n"
                "What are you interested in?\n\n"
                "For example: AI, technology, startups, "
                "stocks, financial news, or anything else you follow.\n\n"
                "Tell me as many as you like, or say \"skip\"."
            ),

            "ASK_MARKET_PREFERENCES": (
                "Got it! 📊\n\n"
                "Which markets or financial areas do you care about?\n\n"
                "For example: Indian stocks, US stocks, ETFs, "
                "IPOs, crypto, sectors, or the economy.\n\n"
                "You can also say \"skip\"."
            ),

            "ASK_WATCHLIST": (
                "Anything specific you want me to watch? 🔎\n\n"
                "You can name companies, stocks, sectors, or markets.\n\n"
                "For example: NVIDIA, Microsoft, semiconductors, "
                "or Indian markets.\n\n"
                "Nothing specific? Just say \"skip\"."
            ),

            "ASK_INSIGHT_PREFERENCES": (
                "When something important happens, what would you "
                "like to know about? 📰\n\n"
                "For example: earnings, company news, filings, "
                "market-moving events, M&A, or macro news.\n\n"
                "Tell me what would be most useful, or say \"skip\"."
            ),

            "ASK_ALERTS": (
                "Would you like me to watch out for anything? 🔔\n\n"
                "For example: earnings, company announcements, "
                "filings, funding events, or big market moves.\n\n"
                "You can tell me your own alerts, or say \"skip\"."
            ),

            "ASK_DAILY_BRIEFING": (
                "One more thing ☀️\n\n"
                "Would you like a daily briefing from me?\n\n"
                "I'll keep it focused on the things you actually care about.\n\n"
                "Just say yes, no, or skip."
            ),

            "ASK_BRIEFING_TIME": (
                "Perfect! ⏰\n\n"
                "What time would you like your daily briefing?\n\n"
                "For example: 8 AM, 8:30 AM, or 9 PM."
            ),

            "ASK_TIMEZONE": (
                "Almost done! 🌏\n\n"
                "Which timezone should I use for your briefings "
                "and alerts?\n\n"
                "For example: Asia/Kolkata, America/New_York, "
                "or Europe/London.\n\n"
                "You can also say \"skip\"."
            ),
        }

        try:
            return messages[step]

        except KeyError as exc:
            raise ValueError(
                f"No onboarding message defined for step: {step}"
            ) from exc



