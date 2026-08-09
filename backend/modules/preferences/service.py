from datetime import datetime, time
from typing import Any
from uuid import UUID

from backend.modules.preferences.schemas import (
    PreferenceChange,
    PreferenceResult,
)


class PreferenceService:
    """
    Deterministic preference-management state machine.

    The service handles conversational preference changes.

    Important:
    - Existing preferences are shown before modification.
    - A requested change is represented as a PreferenceChange.
    - Database persistence happens ONLY after explicit confirmation.
    - Repository methods do not own the transaction.
    """

    # ============================================================
    # CONSTRUCTOR
    # ============================================================

    def __init__(
        self,
        *,
        profile_repository,
    ):
        self._profile_repository = profile_repository

    # ============================================================
    # START
    # ============================================================

    async def start(
        self,
        *,
        user_id: UUID,
    ) -> PreferenceResult:
        """
        Start the preference-management flow.

        The user's current profile is loaded and displayed.
        """

        profile = await self._profile_repository.get_by_user_id(
            user_id
        )

        if profile is None:
            return PreferenceResult(
                step="NO_PROFILE",
                message=(
                    "I couldn't find your preference profile yet. "
                    "Let's get that set up first."
                ),
                completed=True,
            )

        return PreferenceResult(
            step="SELECT_PREFERENCE",
            message=self._preference_summary(profile),
            completed=False,
        )

    # ============================================================
    # RESPONSE HANDLER
    # ============================================================

    async def handle_response(
        self,
        *,
        user_id: UUID,
        profile,
        step: str,
        response: str,
        pending_change: PreferenceChange | None = None,
    ) -> PreferenceResult:
        """
        Handle one user response in the preference state machine.

        The caller is responsible for preserving pending_change
        between conversational turns.
        """

        response = response.strip()

        # --------------------------------------------------------
        # SELECT PREFERENCE
        # --------------------------------------------------------

        if step == "SELECT_PREFERENCE":
            return self._handle_preference_selection(
                profile=profile,
                response=response,
            )

        # --------------------------------------------------------
        # EDIT ROLE
        # --------------------------------------------------------

        if step == "EDIT_ROLE":
            return self._build_change(
                field="role",
                old_value=profile.role,
                new_value=response,
            )

        # --------------------------------------------------------
        # EDIT INTERESTS
        # --------------------------------------------------------

        if step == "EDIT_INTERESTS":
            interests = self._parse_list(response)

            if not interests:
                return PreferenceResult(
                    step="EDIT_INTERESTS",
                    message=(
                        "Of course. What interests would you like "
                        "Atlas to keep for you?\n\n"
                        "For example: AI, technology, startups."
                    ),
                )

            return self._build_change(
                field="interests",
                old_value=profile.interests,
                new_value=interests,
            )

        # --------------------------------------------------------
        # EDIT MARKET PREFERENCES
        # --------------------------------------------------------

        if step == "EDIT_MARKET_PREFERENCES":
            preferences = self._parse_list(response)

            if not preferences:
                return PreferenceResult(
                    step="EDIT_MARKET_PREFERENCES",
                    message=(
                        "What markets or asset types would you like "
                        "me to focus on?\n\n"
                        "For example: US stocks, Indian equities, ETFs."
                    ),
                )

            return self._build_change(
                field="market_preferences",
                old_value=profile.market_preferences,
                new_value=preferences,
            )

        # --------------------------------------------------------
        # EDIT TRACKED ENTITIES / WATCHLIST
        # --------------------------------------------------------

        if step == "EDIT_TRACKED_ENTITIES":
            entities = self._parse_list(response)

            if not entities:
                return PreferenceResult(
                    step="EDIT_TRACKED_ENTITIES",
                    message=(
                        "Which companies, stocks, or other entities "
                        "would you like Atlas to track?\n\n"
                        "For example: NVIDIA, Microsoft, TCS."
                    ),
                )

            return self._build_change(
                field="tracked_entities",
                old_value=profile.tracked_entities,
                new_value=entities,
            )

        # --------------------------------------------------------
        # EDIT INSIGHT PREFERENCES
        # --------------------------------------------------------

        if step == "EDIT_INSIGHT_PREFERENCES":
            preferences = self._parse_list(response)

            if not preferences:
                return PreferenceResult(
                    step="EDIT_INSIGHT_PREFERENCES",
                    message=(
                        "What kind of insights would you like more of?\n\n"
                        "For example: earnings, company news, "
                        "valuation, market trends."
                    ),
                )

            return self._build_change(
                field="insight_preferences",
                old_value=profile.insight_preferences,
                new_value=preferences,
            )

        # --------------------------------------------------------
        # EDIT ALERT PREFERENCES
        # --------------------------------------------------------

        if step == "EDIT_ALERT_PREFERENCES":
            preferences = self._parse_list(response)

            if not preferences:
                return PreferenceResult(
                    step="EDIT_ALERT_PREFERENCES",
                    message=(
                        "What should Atlas alert you about?\n\n"
                        "For example: large market moves, "
                        "earnings surprises, or major company news."
                    ),
                )

            return self._build_change(
                field="alert_preferences",
                old_value=profile.alert_preferences,
                new_value=preferences,
            )

        # --------------------------------------------------------
        # EDIT BRIEFING ENABLED
        # --------------------------------------------------------

        if step == "EDIT_BRIEFING_ENABLED":
            normalized = response.lower()

            if normalized in {
                "yes",
                "y",
                "enable",
                "enabled",
                "on",
                "turn on",
                "true",
            }:
                new_value = True

            elif normalized in {
                "no",
                "n",
                "disable",
                "disabled",
                "off",
                "turn off",
                "false",
            }:
                new_value = False

            else:
                return PreferenceResult(
                    step="EDIT_BRIEFING_ENABLED",
                    message=(
                        "Would you like your daily briefings "
                        "enabled or disabled?"
                    ),
                    completed=False,
                )

            return self._build_change(
                field="briefing_enabled",
                old_value=profile.briefing_enabled,
                new_value=new_value,
            )

        # --------------------------------------------------------
        # EDIT BRIEFING TIME
        # --------------------------------------------------------

        if step == "EDIT_BRIEFING_TIME":
            parsed_time = self._parse_time(response)

            if parsed_time is None:
                return PreferenceResult(
                    step="EDIT_BRIEFING_TIME",
                    message=(
                        "What time would you like your daily briefing?\n\n"
                        "For example: 8:00 AM or 9:30 PM."
                    ),
                    completed=False,
                )

            return self._build_change(
                field="briefing_time",
                old_value=profile.briefing_time,
                new_value=parsed_time.strftime("%H:%M"),
            )

        # --------------------------------------------------------
        # EDIT TIMEZONE
        # --------------------------------------------------------

        if step == "EDIT_TIMEZONE":
            if not response:
                return PreferenceResult(
                    step="EDIT_TIMEZONE",
                    message=(
                        "What timezone should I use for your briefings?\n\n"
                        "For example: Asia/Kolkata."
                    ),
                    completed=False,
                )

            return self._build_change(
                field="timezone",
                old_value=profile.timezone,
                new_value=response,
            )

        # --------------------------------------------------------
        # CONFIRM CHANGE
        # --------------------------------------------------------

        if step == "CONFIRM_CHANGE":
            return await self._handle_confirmation(
                user_id=user_id,
                response=response,
                pending_change=pending_change,
            )

        raise ValueError(
            f"Unknown preference step: {step}"
        )

    # ============================================================
    # PREFERENCE SELECTION
    # ============================================================

    def _handle_preference_selection(
        self,
        *,
        profile,
        response: str,
    ) -> PreferenceResult:

        normalized = self._normalize(response)

        aliases = {
            "role": "EDIT_ROLE",
            "name": "EDIT_ROLE",

            "interest": "EDIT_INTERESTS",
            "interests": "EDIT_INTERESTS",
            "topics": "EDIT_INTERESTS",
            "things i like": "EDIT_INTERESTS",

            "market": "EDIT_MARKET_PREFERENCES",
            "markets": "EDIT_MARKET_PREFERENCES",
            "market preferences": "EDIT_MARKET_PREFERENCES",
            "assets": "EDIT_MARKET_PREFERENCES",

            "watchlist": "EDIT_TRACKED_ENTITIES",
            "tracked companies": "EDIT_TRACKED_ENTITIES",
            "companies": "EDIT_TRACKED_ENTITIES",
            "stocks": "EDIT_TRACKED_ENTITIES",
            "companies i follow": "EDIT_TRACKED_ENTITIES",

            "insights": "EDIT_INSIGHT_PREFERENCES",
            "insight": "EDIT_INSIGHT_PREFERENCES",
            "research": "EDIT_INSIGHT_PREFERENCES",

            "alerts": "EDIT_ALERT_PREFERENCES",
            "alert": "EDIT_ALERT_PREFERENCES",
            "notifications": "EDIT_ALERT_PREFERENCES",

            "briefing": "EDIT_BRIEFING_ENABLED",
            "briefings": "EDIT_BRIEFING_ENABLED",
            "daily briefing": "EDIT_BRIEFING_ENABLED",
            "daily briefings": "EDIT_BRIEFING_ENABLED",

            "briefing time": "EDIT_BRIEFING_TIME",
            "briefing timing": "EDIT_BRIEFING_TIME",
            "time for briefing": "EDIT_BRIEFING_TIME",

            "timezone": "EDIT_TIMEZONE",
            "time zone": "EDIT_TIMEZONE",
        }

        selected_step = aliases.get(normalized)

        if selected_step is None:
            return PreferenceResult(
                step="SELECT_PREFERENCE",
                message=(
                    "Of course — what would you like to change?\n\n"
                    f"{self._preference_summary(profile)}"
                ),
                completed=False,
            )

        return self._message_for_edit_step(
            step=selected_step,
            profile=profile,
        )

    # ============================================================
    # BUILD CHANGE
    # ============================================================

    def _build_change(
        self,
        *,
        field: str,
        old_value: Any,
        new_value: Any,
    ) -> PreferenceResult:

        change = PreferenceChange(
            field=field,
            old_value=old_value,
            new_value=new_value,
        )

        return PreferenceResult(
            step="CONFIRM_CHANGE",
            message=self._confirmation_message(change),
            completed=False,
        )

    # ============================================================
    # CONFIRMATION
    # ============================================================

    async def _handle_confirmation(
        self,
        *,
        user_id: UUID,
        response: str,
        pending_change: PreferenceChange | None,
    ) -> PreferenceResult:

        if pending_change is None:
            raise ValueError(
                "Cannot confirm a preference change "
                "without a pending change."
            )

        normalized = response.lower()

        if normalized in {
            "yes",
            "y",
            "confirm",
            "save",
            "save it",
            "do it",
        }:
            await self._persist_change(
                user_id=user_id,
                change=pending_change,
            )

            return PreferenceResult(
                step="UPDATED",
                message=(
                    "Done! 😊\n\n"
                    f"I've updated your "
                    f"{self._humanize_field(pending_change.field)} "
                    "preference.\n\n"
                    "You can change it again anytime."
                ),
                completed=True,
            )

        if normalized in {
            "no",
            "n",
            "cancel",
            "don't",
            "dont",
            "never mind",
            "nevermind",
        }:
            return PreferenceResult(
                step="SELECT_PREFERENCE",
                message=(
                    "No problem — I won't change anything. 😊\n\n"
                    "Would you like to change another preference?"
                ),
                completed=False,
            )

        return PreferenceResult(
            step="CONFIRM_CHANGE",
            message=(
                "Just to make sure I understood you correctly — "
                "should I save this change?\n\n"
                "Please say yes or no."
            ),
            completed=False,
        )

    # ============================================================
    # PERSISTENCE
    # ============================================================

    async def _persist_change(
        self,
        *,
        user_id: UUID,
        change: PreferenceChange,
    ) -> None:

        field = change.field
        value = change.new_value

        if field == "briefing_time":
            if isinstance(value, str):
                parsed_time = self._parse_time(value)

                if parsed_time is None:
                    raise ValueError(
                        f"Invalid briefing time: {value}"
                    )

                value = parsed_time

        kwargs = {
            field: value,
        }

        await self._profile_repository.create_or_update_profile(
            user_id=user_id,
            **kwargs,
        )

    # ============================================================
    # EDIT MESSAGES
    # ============================================================

    def _message_for_edit_step(
        self,
        *,
        step: str,
        profile,
    ) -> PreferenceResult:

        if step == "EDIT_ROLE":
            return PreferenceResult(
                step=step,
                message=(
                    "You're currently listed as "
                    f"**{self._display_value(profile.role)}**.\n\n"
                    "Would you like to change that?"
                ),
            )

        if step == "EDIT_INTERESTS":
            return PreferenceResult(
                step=step,
                message=(
                    "Here are the interests I currently have for you:\n\n"
                    f"**{self._display_value(profile.interests)}**\n\n"
                    "What would you like me to change them to?"
                ),
            )

        if step == "EDIT_MARKET_PREFERENCES":
            return PreferenceResult(
                step=step,
                message=(
                    "You're currently interested in:\n\n"
                    f"**{self._display_value(profile.market_preferences)}**\n\n"
                    "What markets or asset types would you like "
                    "me to focus on instead?"
                ),
            )

        if step == "EDIT_TRACKED_ENTITIES":
            return PreferenceResult(
                step=step,
                message=(
                    "You're currently tracking:\n\n"
                    f"**{self._display_value(profile.tracked_entities)}**\n\n"
                    "Which companies or entities would you like "
                    "to add, remove, or replace?"
                ),
            )

        if step == "EDIT_INSIGHT_PREFERENCES":
            return PreferenceResult(
                step=step,
                message=(
                    "You currently prefer insights about:\n\n"
                    f"**{self._display_value(profile.insight_preferences)}**\n\n"
                    "What would you like to change?"
                ),
            )

        if step == "EDIT_ALERT_PREFERENCES":
            return PreferenceResult(
                step=step,
                message=(
                    "Your current alerts are focused on:\n\n"
                    f"**{self._display_value(profile.alert_preferences)}**\n\n"
                    "What would you like Atlas to alert you about?"
                ),
            )

        if step == "EDIT_BRIEFING_ENABLED":
            current = self._display_value(
                profile.briefing_enabled
            )

            return PreferenceResult(
                step=step,
                message=(
                    "Your daily briefing is currently "
                    f"**{current}**.\n\n"
                    "Would you like it enabled or disabled?"
                ),
            )

        if step == "EDIT_BRIEFING_TIME":
            return PreferenceResult(
                step=step,
                message=(
                    "Your daily briefing is currently scheduled for "
                    f"**{self._display_value(profile.briefing_time)}**.\n\n"
                    "What time would you prefer?"
                ),
            )

        if step == "EDIT_TIMEZONE":
            return PreferenceResult(
                step=step,
                message=(
                    "I'm currently using **"
                    f"{self._display_value(profile.timezone)}"
                    "** for your briefing timezone.\n\n"
                    "What timezone should I use instead?"
                ),
            )

        raise ValueError(
            f"Unknown preference edit step: {step}"
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def _preference_summary(
        self,
        profile,
    ) -> str:

        return (
            "Of course! 😊 Here are the preferences I currently "
            "have for you:\n\n"
            f"**Role:** "
            f"{self._display_value(profile.role)}\n\n"
            f"**Interests:** "
            f"{self._display_value(profile.interests)}\n\n"
            f"**Markets:** "
            f"{self._display_value(profile.market_preferences)}\n\n"
            f"**Watchlist:** "
            f"{self._display_value(profile.tracked_entities)}\n\n"
            f"**Insights:** "
            f"{self._display_value(profile.insight_preferences)}\n\n"
            f"**Alerts:** "
            f"{self._display_value(profile.alert_preferences)}\n\n"
            f"**Daily briefing:** "
            f"{self._display_value(profile.briefing_enabled)}\n\n"
            f"**Briefing time:** "
            f"{self._display_value(profile.briefing_time)}\n\n"
            f"**Timezone:** "
            f"{self._display_value(profile.timezone)}\n\n"
            "Which one would you like to change?"
        )

    # ============================================================
    # CONFIRMATION MESSAGE
    # ============================================================

    @classmethod
    def _confirmation_message(
        cls,
        change: PreferenceChange,
    ) -> str:

        return (
            "Got it! 😊\n\n"
            f"**{cls._humanize_field(change.field)}**\n"
            f"Current: "
            f"{cls._display_value(change.old_value)}\n"
            f"New: "
            f"{cls._display_value(change.new_value)}\n\n"
            "Should I save this change?"
        )

    # ============================================================
    # VALUE PARSING
    # ============================================================

    @staticmethod
    def _parse_list(
        value: str,
    ) -> list[str]:

        seen: set[str] = set()
        result: list[str] = []

        for item in value.split(","):
            cleaned = item.strip()

            if not cleaned:
                continue

            normalized = cleaned.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(cleaned)

        return result

    @staticmethod
    def _parse_time(
        value: str,
    ) -> time | None:

        normalized = value.strip().upper()

        formats = [
            "%I:%M %p",
            "%I %p",
            "%H:%M",
            "%H",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(
                    normalized,
                    fmt,
                ).time()
            except ValueError:
                continue

        return None

    # ============================================================
    # DISPLAY HELPERS
    # ============================================================

    @staticmethod
    def _display_value(
        value: Any,
    ) -> str:

        # IMPORTANT:
        # bool must be handled before generic falsy values.
        if isinstance(value, bool):
            return "Enabled" if value else "Disabled"

        if value is None:
            return "Not set"

        if isinstance(value, list):
            if not value:
                return "Not set"

            return ", ".join(
                str(item)
                for item in value
            )

        if isinstance(value, time):
            return value.strftime("%H:%M")

        return str(value)

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:

        return " ".join(
            value.lower().strip().split()
        )

    @staticmethod
    def _humanize_field(
        field: str,
    ) -> str:

        names = {
            "role": "Role",
            "interests": "Interests",
            "market_preferences": "Market preferences",
            "tracked_entities": "Watchlist",
            "insight_preferences": "Insight preferences",
            "alert_preferences": "Alert preferences",
            "briefing_enabled": "Daily briefing",
            "briefing_time": "Briefing time",
            "timezone": "Timezone",
        }

        return names.get(
            field,
            field.replace("_", " ").title(),
        )