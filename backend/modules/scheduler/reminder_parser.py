from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class ReminderRequest:
    reminder_text: str
    delay_seconds: int


class ReminderParser:
    """
    Deterministic parser for simple natural-language
    relative reminders.

    Examples:

        Remind me about NVIDIA earnings in 2 minutes
        Remind me to check earnings in 10 minutes
        Notify me about the Fed in 1 hour
        Alert me about Tesla earnings after 30 minutes
    """

    _PATTERN = re.compile(
        r"""
        ^\s*
        (?:
            remind\s+me
            |
            notify\s+me
            |
            alert\s+me
        )
        \s+
        (?P<message>.+?)
        \s+
        (?:in|after)
        \s+
        (?P<amount>\d+)
        \s*
        (?P<unit>
            second(?:s)?
            |
            minute(?:s)?
            |
            hour(?:s)?
        )
        \s*$
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    _UNIT_SECONDS = {
        "second": 1,
        "seconds": 1,
        "minute": 60,
        "minutes": 60,
        "hour": 3600,
        "hours": 3600,
    }

    _LEADING_FILLERS = (
        "about ",
        "to ",
        "for ",
        "on ",
    )

    def parse(
        self,
        text: str,
    ) -> ReminderRequest | None:
        if not text or not text.strip():
            return None

        match = self._PATTERN.match(
            text.strip()
        )

        if not match:
            return None

        message = match.group("message").strip()

        for prefix in self._LEADING_FILLERS:
            if message.lower().startswith(prefix):
                message = message[len(prefix):].strip()
                break

        amount = int(
            match.group("amount")
        )

        unit = match.group(
            "unit"
        ).lower()

        if not message:
            return None

        delay_seconds = amount * self._UNIT_SECONDS[unit]

        return ReminderRequest(
            reminder_text=message,
            delay_seconds=delay_seconds,
        )