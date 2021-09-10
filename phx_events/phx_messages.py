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
    """Protocol describing a handler that will be called using the provided executor pool"""

    def __call__(self, __message: Union['PHXMessage', 'PHXEventMessage'], __client: 'PHXChannelsClient') -> None:
        """
        Args:
            __message (Union[PHXMessage, PHXEventMessage]): The message the handler should process
            __client (PHXChannelsClient): The client instance
        """
        ...  # pragma: no cover


class CoroutineHandler(Protocol):
    """Protocol describing a handler that will be run as a task in the event loop"""

    async def __call__(self, __message: Union['PHXMessage', 'PHXEventMessage'], __client: 'PHXChannelsClient') -> None:
        """
        Args:
            __message (Union[PHXMessage, PHXEventMessage]): The message the handler should process
            __client (PHXChannelsClient): The client instance
        """
        ...  # pragma: no cover


ChannelHandlerFunction = Union[ExecutorHandler, CoroutineHandler]


@dataclass()
class EventHandlerConfig:
    """
    Args:
        queue (asyncio.Queue): The queue that messages are passed into and the event handlers are fed from
        default_handlers (list[ChannelHandlerFunction]): Handler functions that should always be run for the specified
                                                         event.
        topic_handlers (dict[Topic, list[ChannelHandlerFunction]]): Handler functions that should be run only for the
                                                                    topics specified in the mapping.
        task (asyncio.Task): The task that consumes off the `queue` and determines which `default_handlers` and
                             `topic_handlers` to run.
    """
    queue: asyncio.Queue[ChannelMessage]
    default_handlers: list[ChannelHandlerFunction]
    topic_handlers: dict[Topic, list[ChannelHandlerFunction]]
    task: asyncio.Task[None]


@unique
class PHXEvent(Enum):
    """Phoenix Channels admin events"""
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
