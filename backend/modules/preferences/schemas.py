
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PreferenceResult:
    """
    Result returned by the preference-management state machine.
    """

    step: str
    message: str
    completed: bool = False


@dataclass(frozen=True)
class PreferenceChange:
    """
    Represents a proposed preference modification.

    The change is only persisted after the user explicitly
    confirms it.
    """

    field: str
    old_value: Any
    new_value: Any

