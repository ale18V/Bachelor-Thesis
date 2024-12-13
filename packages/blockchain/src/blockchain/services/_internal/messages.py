import asyncio
from typing import Optional
from ...generated import peer_pb2
from ...models import Message, AbstractMessageService
import loguru


class MessageService(AbstractMessageService):
    def __init__(self) -> None:
        self.queues: dict[int, asyncio.Queue[Message]] = {}

    async def put(self, message: Message) -> None:
        if isinstance(message, peer_pb2.ProposeBlockRequest):
            height = message.block.header.height
        else:
            height = message.height

        if height not in self.queues:
            self.queues[height] = asyncio.Queue()

        await self.queues[height].put(message)

    async def get(self, height: int, timeout: Optional[int] = None) -> Optional[Message]:
        if height not in self.queues:
            self.queues[height] = asyncio.Queue()
        try:
            loguru.logger.debug(f"Polling messages for height {height}")
            return await asyncio.wait_for(self.queues[height].get(), timeout)
        except asyncio.TimeoutError:
            return None

    def empty(self, height: int) -> bool:
        return height not in self.queues or self.queues[height].empty()
