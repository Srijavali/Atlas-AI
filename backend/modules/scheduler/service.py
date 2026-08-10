from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select

from backend.modules.background.worker import (
    BackgroundJob,
    BackgroundWorker,
)
from backend.modules.brain.service import AtlasAgent
from backend.modules.notifications.service import (
    NotificationService,
)
from backend.persistence.database import AsyncSessionFactory
from backend.persistence.models.profile import UserProfileModel
from backend.persistence.models.user import UserModel


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ScheduledReminder:
    job_id: str
    telegram_user_id: int
    message: str
    run_at: datetime


class SchedulerService:
    """
    Atlas asynchronous scheduler.

    Supports:

    1. One-time reminders
       "Remind me about NVIDIA in 2 minutes"

    2. Daily briefings
       User-configured briefing time + timezone.

    The scheduler decides WHEN work is due.

    The background worker decides HOW the work executes.
    """

    def __init__(
        self,
        *,
        worker: BackgroundWorker,
        atlas_agent: AtlasAgent,
        notification_service: NotificationService,
    ) -> None:
        self._worker = worker
        self._atlas_agent = atlas_agent
        self._notification_service = notification_service

        self._running = False
        self._loop_task: asyncio.Task[None] | None = None

        self._reminders: dict[
            str,
            ScheduledReminder,
        ] = {}

        self._completed_briefings: set[str] = set()

    # =========================================================
    # LIFECYCLE
    # =========================================================

    async def start(self) -> None:
        if self._running:
            return

        self._running = True

        self._loop_task = asyncio.create_task(
            self._scheduler_loop()
        )

        logger.info(
            "Atlas scheduler started"
        )

    async def stop(self) -> None:
        self._running = False

        if self._loop_task is not None:
            self._loop_task.cancel()

            await asyncio.gather(
                self._loop_task,
                return_exceptions=True,
            )

            self._loop_task = None

        self._reminders.clear()

        logger.info(
            "Atlas scheduler stopped"
        )

    # =========================================================
    # ONE-TIME REMINDERS
    # =========================================================

    async def schedule_reminder(
        self,
        *,
        telegram_user_id: int,
        message: str,
        delay_seconds: int,
    ) -> str:
        """
        Schedule a one-time Telegram reminder.

        Example:

            delay_seconds=120

        means the reminder will run approximately
        two minutes from now.
        """

        if not self._running:
            raise RuntimeError(
                "Scheduler is not running"
            )

        if delay_seconds <= 0:
            raise ValueError(
                "Reminder delay must be greater than zero"
            )

        if not message or not message.strip():
            raise ValueError(
                "Reminder message cannot be empty"
            )

        job_id = str(uuid.uuid4())

        run_at = (
            datetime.now()
            + timedelta(seconds=delay_seconds)
        )

        reminder = ScheduledReminder(
            job_id=job_id,
            telegram_user_id=telegram_user_id,
            message=message.strip(),
            run_at=run_at,
        )

        self._reminders[job_id] = reminder

        logger.info(
            "Reminder scheduled: job=%s user=%s run_at=%s",
            job_id,
            telegram_user_id,
            run_at.isoformat(),
        )

        return job_id

    async def cancel_reminder(
        self,
        job_id: str,
    ) -> bool:
        """
        Cancel a pending in-memory reminder.
        """

        if job_id not in self._reminders:
            return False

        del self._reminders[job_id]

        logger.info(
            "Reminder cancelled: job=%s",
            job_id,
        )

        return True

    # =========================================================
    # SCHEDULER LOOP
    # =========================================================

    async def _scheduler_loop(self) -> None:
        """
        Main asynchronous scheduling loop.

        One-time reminders are checked every second so a
        two-minute demo reminder fires promptly.

        Daily briefings are checked on the same loop.
        """

        while self._running:
            try:
                await self._process_due_reminders()
                await self.check_due_briefings()

            except asyncio.CancelledError:
                break

            except Exception:
                logger.exception(
                    "Scheduler cycle failed"
                )

            await asyncio.sleep(1)

    # =========================================================
    # ONE-TIME REMINDER EXECUTION
    # =========================================================

    async def _process_due_reminders(self) -> None:
        now = datetime.now()

        due_reminders = [
            reminder
            for reminder in self._reminders.values()
            if reminder.run_at <= now
        ]

        for reminder in due_reminders:
            self._reminders.pop(
                reminder.job_id,
                None,
            )

            await self._worker.enqueue(
                BackgroundJob(
                    job_id=reminder.job_id,
                    handler=lambda reminder=reminder: (
                        self._execute_reminder(
                            reminder
                        )
                    ),
                )
            )

            logger.info(
                "Reminder moved to background worker: job=%s",
                reminder.job_id,
            )

    async def _execute_reminder(
        self,
        reminder: ScheduledReminder,
    ) -> None:
        """
        Execute a reminder after it becomes due.

        For the MVP, the reminder message itself is sent.
        This makes the behavior deterministic and reliable.

        Later, the message can be passed through Atlas/tool
        execution before delivery if the reminder requires
        fresh information.
        """

        notification = (
            "🔔 Atlas Reminder\n\n"
            f"{reminder.message}"
        )

        await self._notification_service.send_text(
            telegram_user_id=reminder.telegram_user_id,
            message=notification,
        )

        logger.info(
            "Reminder delivered: job=%s user=%s",
            reminder.job_id,
            reminder.telegram_user_id,
        )

    # =========================================================
    # DAILY BRIEFINGS
    # =========================================================

    async def check_due_briefings(self) -> None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(
                    UserModel,
                    UserProfileModel,
                )
                .join(
                    UserProfileModel,
                    UserProfileModel.user_id
                    == UserModel.id,
                )
                .where(
                    UserProfileModel.briefing_enabled.is_(True),
                    UserProfileModel.briefing_time.is_not(None),
                    UserProfileModel.timezone.is_not(None),
                )
            )

            rows = result.all()

        for user, profile in rows:

            if not self._is_due(profile):
                continue

            job_key = self._briefing_job_key(
                user.id,
                profile,
            )

            if job_key in self._completed_briefings:
                continue

            job_id = str(uuid.uuid4())

            async def execute_briefing(
                user=user,
                profile=profile,
                job_key=job_key,
            ) -> None:
                await self._generate_and_send_briefing(
                    user,
                    profile,
                )

                self._completed_briefings.add(
                    job_key
                )

            await self._worker.enqueue(
                BackgroundJob(
                    job_id=job_id,
                    handler=execute_briefing,
                )
            )

            logger.info(
                "Daily briefing queued: user=%s job=%s",
                user.id,
                job_id,
            )

    @staticmethod
    def _is_due(
        profile: UserProfileModel,
    ) -> bool:
        if not profile.briefing_enabled:
            return False

        if profile.briefing_time is None:
            return False

        if not profile.timezone:
            return False

        try:
            timezone = ZoneInfo(
                profile.timezone
            )

        except ZoneInfoNotFoundError:
            logger.warning(
                "Invalid timezone: %s",
                profile.timezone,
            )
            return False

        now = datetime.now(timezone)
        configured_time = profile.briefing_time

        return (
            now.hour == configured_time.hour
            and now.minute == configured_time.minute
        )

    @staticmethod
    def _briefing_job_key(
        user_id,
        profile: UserProfileModel,
    ) -> str:
        timezone = ZoneInfo(
            profile.timezone
        )

        today = datetime.now(
            timezone
        ).date()

        return (
            f"daily-briefing:"
            f"{user_id}:"
            f"{today.isoformat()}"
        )

    async def _generate_and_send_briefing(
        self,
        user: UserModel,
        profile: UserProfileModel,
    ) -> None:
        context = {
            "name": user.display_name,
            "role": profile.role,
            "interests": profile.interests,
            "market_preferences": (
                profile.market_preferences
            ),
            "tracked_entities": (
                profile.tracked_entities
            ),
            "insight_preferences": (
                profile.insight_preferences
            ),
            "alert_preferences": (
                profile.alert_preferences
            ),
        }

        prompt = self._build_briefing_prompt(
            context
        )

        logger.info(
            "Generating daily briefing for user=%s",
            user.telegram_user_id,
        )

        response = (
            await self._atlas_agent.intelligent_response(
                text=prompt,
                user_context=context,
            )
        )

        await self._notification_service.send_text(
            telegram_user_id=user.telegram_user_id,
            message=response,
        )

    @staticmethod
    def _build_briefing_prompt(
        context: dict,
    ) -> str:
        return f"""
You are Atlas preparing a personalized daily briefing.

User context:
{context}

Create a concise and useful briefing based on the
user's interests, market preferences, tracked entities,
insight preferences, and alert preferences.

Prioritize genuinely relevant information.

When current information is required, use the
appropriate Atlas tools.

Do not invent current facts.

Structure the response clearly for Telegram.

Avoid generic filler and unnecessary repetition.
""".strip()