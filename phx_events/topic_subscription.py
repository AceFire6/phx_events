from asyncio import Event
from dataclasses import dataclass
from enum import IntEnum, unique
from typing import Optional

from phx_events.phx_messages import PHXEventMessage


@unique
class SubscriptionStatus(IntEnum):
    FAILED = 0
    SUCCESS = 1


@dataclass(frozen=True)
class TopicSubscribeResult:
    status: SubscriptionStatus
    result_message: PHXEventMessage


@dataclass()
class TopicRegistration:
    connection_ref: str
    status_updated_event: Event
    status: Optional[TopicSubscribeResult] = None
