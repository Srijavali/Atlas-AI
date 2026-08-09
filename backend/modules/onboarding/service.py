
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.persistence.models.onboarding import SessionStatus
from backend.persistence.models.user import OnboardingStatus


@dataclass(frozen=True)
class OnboardingResult:
    step: str
    message: str
    completed: bool = False


class OnboardingService:
    """
    Deterministic onboarding state machine.

    The service owns onboarding behavior and delegates persistence
    to the repositories. Repositories do not commit transactions.
    """

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

    async def start(self, user_id: UUID) -> OnboardingResult:
        session = await self._onboarding_repository.get_by_user_id(
            user_id
        )

        if session is not None:
            return OnboardingResult(
                step=session.current_step,
                message=self._message_for_step(
                    session.current_step
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
        current_step = session.current_step
        response = response.strip()

        if current_step == "WELCOME":
            return await self._move_to_step(
                session,
                "ASK_NAME",
            )

        if current_step == "ASK_NAME":
            if not response:
                return OnboardingResult(
                    step="ASK_NAME",
                    message=(
                        "I didn't catch your name. "
                        "What should I call you?"
                    ),
                )

            temporary_data = dict(
                session.temporary_data or {}
            )
            temporary_data["display_name"] = response

            return await self._move_to_step(
                session,
                "ASK_TIMEZONE",
                temporary_data=temporary_data,
            )

        if current_step == "ASK_TIMEZONE":
            if not response:
                return OnboardingResult(
                    step="ASK_TIMEZONE",
                    message=(
                        "Please provide your timezone, "
                        "for example: Asia/Kolkata."
                    ),
                )

            temporary_data = dict(
                session.temporary_data or {}
            )
            temporary_data["timezone"] = response

            return await self._move_to_step(
                session,
                "ASK_INTERESTS",
                temporary_data=temporary_data,
            )

        if current_step == "ASK_INTERESTS":
            if not response:
                return OnboardingResult(
                    step="ASK_INTERESTS",
                    message=(
                        "Tell me at least one interest, "
                        "such as AI, technology, or startups."
                    ),
                )

            interests = [
                item.strip()
                for item in response.split(",")
                if item.strip()
            ]

            if not interests:
                return OnboardingResult(
                    step="ASK_INTERESTS",
                    message=(
                        "Please provide at least one interest."
                    ),
                )

            temporary_data = dict(
                session.temporary_data or {}
            )
            temporary_data["interests"] = interests

            return await self._move_to_step(
                session,
                "ASK_BRIEFING",
                temporary_data=temporary_data,
            )

        if current_step == "ASK_BRIEFING":
            normalized = response.lower()

            if normalized not in {
                "yes",
                "y",
                "no",
                "n",
            }:
                return OnboardingResult(
                    step="ASK_BRIEFING",
                    message=(
                        "Please answer yes or no. "
                        "Would you like Atlas to send briefings?"
                    ),
                )

            briefing_enabled = normalized in {"yes", "y"}

            temporary_data = dict(
                session.temporary_data or {}
            )
            temporary_data["briefing_enabled"] = (
                briefing_enabled
            )

            await self._profile_repository.create_or_update_profile(
                user_id=session.user_id,
                interests=temporary_data.get("interests"),
                timezone_str=temporary_data.get("timezone"),
                briefing_enabled=briefing_enabled,
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
                message=self._message_for_step("COMPLETED"),
                completed=True,
            )

        raise ValueError(
            f"Unknown onboarding step: {current_step}"
        )

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
            message=self._message_for_step(next_step),
        )

    @staticmethod
    def _message_for_step(step: str) -> str:
        messages = {
            "WELCOME": (
                "Hi! I'm Atlas. 👋\n\n"
                "I'm your personal AI assistant. "
                "Let's get you set up.\n\n"
                "What should I call you?"
            ),
            "ASK_NAME": (
                "What should I call you?"
            ),
            "ASK_TIMEZONE": (
                "Nice to meet you! 🌟\n\n"
                "What timezone are you in?\n"
                "For example: Asia/Kolkata."
            ),
            "ASK_INTERESTS": (
                "Great! What are you interested in?\n\n"
                "You can give me multiple interests, "
                "separated by commas."
            ),
            "ASK_BRIEFING": (
                "One last thing: would you like Atlas "
                "to send you regular briefings?\n\n"
                "Please answer yes or no."
            ),
            "COMPLETED": (
                "You're all set! 🎉\n\n"
                "I'm Atlas. How can I help you?"
            ),
        }

        try:
            return messages[step]
        except KeyError as exc:
            raise ValueError(
                f"No onboarding message defined for step: {step}"
            ) from exc

