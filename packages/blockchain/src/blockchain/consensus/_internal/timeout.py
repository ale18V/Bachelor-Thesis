import asyncio
from typing import Awaitable, Callable, Generic, Optional, ParamSpec, TypeVar
import loguru
from ...utils import after_timeout, enqueue

R = TypeVar("R")
P = ParamSpec("P")


class Timeout(Generic[P, R]):
    """A timeout object that can be scheduled to trigger a callback after a certain duration."""

    def __init__(self, callback: Callable[P, Awaitable[R]], duration: int, message: Optional[str] = None) -> None:
        self.callback = callback
        self.duration = duration
        self.message = message

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return await self.callback(*args, **kwargs)


class TimeoutManager:

    def __init__(self, timeouts: dict[str, Timeout[[int, int], None]]) -> None:
        self.timeouts = timeouts
        self.scheduled_timeouts: dict[str, dict[tuple[int, int], asyncio.Task[None]]] = {k: {} for k in timeouts.keys()}

    def schedule(self, state: str, height: int, round: int) -> None:
        """Schedules a callback to be triggered after a timeout expires."""

        timeout = self.timeouts[state]

        @enqueue
        @after_timeout(timeout=timeout.duration, message=timeout.message)
        @loguru.logger.catch
        async def __schedule(timeout: Timeout, height: int, round: int) -> None:
            if timeout.message:
                loguru.logger.info(timeout.message)
            await timeout(height, round)
            self.scheduled_timeouts[state].pop((height, round), None)

        if self.is_scheduled(state, height, round):
            return
        self.scheduled_timeouts[state][(height, round)] = __schedule(timeout, height, round)

    def is_scheduled(self, state: str, height: int, round: int) -> bool:
        return bool(self.scheduled_timeouts[state].get((height, round), False))
