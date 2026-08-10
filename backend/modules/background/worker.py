from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BackgroundJob:
    """
    A unit of asynchronous work.
    """

    job_id: str
    handler: Callable[[], Awaitable[None]]


class BackgroundWorker:
    """
    Lightweight in-process asynchronous worker.

    This MVP intentionally does not require Redis, Celery,
    RabbitMQ, or another external queue.
    """

    def __init__(
        self,
        *,
        max_concurrency: int = 2,
    ) -> None:
        self._queue: asyncio.Queue[BackgroundJob] = (
            asyncio.Queue()
        )

        self._max_concurrency = max_concurrency
        self._workers: list[asyncio.Task[None]] = []
        self._running = False

    async def start(self) -> None:
        if self._running:
            return

        self._running = True

        for index in range(self._max_concurrency):
            task = asyncio.create_task(
                self._worker_loop(index)
            )

            self._workers.append(task)

        logger.info(
            "Background worker started with %d workers",
            self._max_concurrency,
        )

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False

        for task in self._workers:
            task.cancel()

        await asyncio.gather(
            *self._workers,
            return_exceptions=True,
        )

        self._workers.clear()

        logger.info("Background worker stopped")

    async def enqueue(
        self,
        job: BackgroundJob,
    ) -> None:
        if not self._running:
            raise RuntimeError(
                "Background worker is not running"
            )

        await self._queue.put(job)

        logger.info(
            "Background job queued: %s",
            job.job_id,
        )

    async def _worker_loop(
        self,
        worker_index: int,
    ) -> None:
        while self._running:
            try:
                job = await self._queue.get()

                try:
                    logger.info(
                        "Worker %d executing job %s",
                        worker_index,
                        job.job_id,
                    )

                    await job.handler()

                    logger.info(
                        "Worker %d completed job %s",
                        worker_index,
                        job.job_id,
                    )

                except Exception:
                    logger.exception(
                        "Background job %s failed",
                        job.job_id,
                    )

                finally:
                    self._queue.task_done()

            except asyncio.CancelledError:
                break

            except Exception:
                logger.exception(
                    "Unexpected background worker error"
                )