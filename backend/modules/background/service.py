from __future__ import annotations

from backend.modules.background.worker import (
    BackgroundWorker,
)


class BackgroundService:
    """
    Application lifecycle wrapper around the background worker.
    """

    def __init__(
        self,
        *,
        worker: BackgroundWorker,
    ) -> None:
        self.worker = worker

    async def start(self) -> None:
        await self.worker.start()

    async def stop(self) -> None:
        await self.worker.stop()