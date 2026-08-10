from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from backend.domain.enums import InteractionType, Platform


class IncomingInteraction(BaseModel):
    interaction_id: str
    platform: Platform
    platform_event_id: str | None = None

    user_id: str
    conversation_id: str

    interaction_type: InteractionType

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    text: str | None = None
    media_reference: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)