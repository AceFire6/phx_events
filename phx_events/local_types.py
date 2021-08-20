from asyncio import Queue, Task
from logging import Logger
from typing import Callable, NewType, Optional, TYPE_CHECKING, TypedDict, Union


if TYPE_CHECKING:
    from phx_events.phx_messages import PHXEvent, PHXEventMessage, PHXMessage


Topic = NewType('Topic', str)
Event = NewType('Event', str)
ChannelEvent = Union['PHXEvent', Event]
ChannelMessage = Union['PHXMessage', 'PHXEventMessage']
HandlerFunction = Callable[[ChannelMessage, Logger], None]


class EventMap(TypedDict):
    queue: Queue[ChannelMessage]
    handlers: list[HandlerFunction]
    task: Task[None]
    topic: Optional[Topic]
