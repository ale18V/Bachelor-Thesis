import asyncio
from enum import Enum
from typing import Any, Callable, Coroutine


class EventType(Enum):
    UPDATE = 1
    VALIDATOR = 4


Listener = Callable[..., Coroutine[Any, Any, None]]
Unsubscriber = Callable[[], None]


class EventBus(object):
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.listeners: dict[EventType, list[Listener]] = {}
        self.loop = loop

    def subscribe(self, event_type: EventType, listener: Listener) -> Unsubscriber:
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
        return lambda: self.listeners[event_type].remove(listener)

    def publish(self, event_type: EventType, data: Any) -> None:
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                self.loop.create_task(listener(data))

    def unsubscribe(self, event_type: EventType, listener: Listener) -> None:
        if event_type in self.listeners:
            self.listeners[event_type].remove(listener)
