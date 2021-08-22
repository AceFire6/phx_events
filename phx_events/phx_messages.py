import asyncio
from dataclasses import dataclass
from enum import Enum, unique
from functools import cached_property
from typing import Any, NewType, Optional, Protocol, TYPE_CHECKING, Union


if TYPE_CHECKING:
    from phx_events.client import PHXChannelsClient


Topic = NewType('Topic', str)
Event = NewType('Event', str)
ChannelEvent = Union['PHXEvent', Event]
ChannelMessage = Union['PHXMessage', 'PHXEventMessage']


class ExecutorHandler(Protocol):
    def __call__(self, __message: Union['PHXMessage', 'PHXEventMessage'], __client: 'PHXChannelsClient') -> None:
        ...


class CoroutineHandler(Protocol):
    async def __call__(self, __message: Union['PHXMessage', 'PHXEventMessage'], __client: 'PHXChannelsClient') -> None:
        ...


ChannelHandlerFunction = Union[ExecutorHandler, CoroutineHandler]


@dataclass()
class EventHandlerConfig:
    queue: asyncio.Queue[ChannelMessage]
    default_handlers: list[ChannelHandlerFunction]
    topic_handlers: dict[Topic, list[ChannelHandlerFunction]]
    task: asyncio.Task[None]


@unique
class PHXEvent(Enum):
    close = 'phx_close'
    error = 'phx_error'
    join = 'phx_join'
    reply = 'phx_reply'
    leave = 'phx_leave'

    # hack for typing
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class BasePHXMessage:
    topic: Topic
    ref: Optional[str]
    payload: dict[str, Any]

    @cached_property
    def subtopic(self) -> Optional[str]:
        if ':' not in self.topic:
            return None

        _, subtopic = self.topic.split(':', 1)
        return subtopic


@dataclass(frozen=True)
class PHXMessage(BasePHXMessage):
    event: Event


@dataclass(frozen=True)
class PHXEventMessage(BasePHXMessage):
    event: PHXEvent
