import asyncio
import hashlib
from typing import Any, Awaitable, Callable, Coroutine, Optional, ParamSpec, TypeVar
import sys
import loguru

from blockchain.generated import peer_pb2


R = TypeVar("R")
P = ParamSpec("P")


def after_timeout(timeout=60, message: Optional[str] = None):  # type: ignore
    """
    Decorator to handle timeouts for the given function.
    @param timeout: timeout in seconds
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @loguru.logger.catch
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            await asyncio.sleep(timeout)
            if message:
                loguru.logger.info(message)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def enqueue(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, asyncio.Task[R]]:
    """
    Decorator to enqueue a function to the event loop.
    """

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> asyncio.Task[R]:
        loop = asyncio.get_event_loop()
        return loop.create_task(func(*args, **kwargs))

    return wrapper


# https://stackoverflow.com/questions/58454190/python-async-waiting-for-stdin-input-while-doing-other-stuff
async def async_input(prompt: Optional[str] = None) -> str:
    stream_reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(stream_reader)
    loop = asyncio.get_running_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    print(prompt)
    try:
        line = await stream_reader.readline()
        return line.decode()
    except KeyboardInterrupt:
        stream_reader.feed_eof()
        return ""


def get_tx_hash(tx: peer_pb2.Transaction) -> str:
    return hashlib.sha256(tx.SerializeToString(deterministic=True)).hexdigest()
