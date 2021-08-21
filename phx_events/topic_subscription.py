from asyncio import Event
from dataclasses import dataclass
from enum import IntEnum, unique
from typing import Optional, TYPE_CHECKING

from phx_events.phx_messages import PHXEventMessage


if TYPE_CHECKING:
    from phx_events.channels_client import PHXChannelsClient


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


async def process_topic_join_reply(message: PHXEventMessage, client: 'PHXChannelsClient') -> None:
    topic = message.topic
    client.logger.info(f'Got topic {topic} join reply {message=}')

    status = SubscriptionStatus.SUCCESS if message.payload['status'] == 'ok' else SubscriptionStatus.FAILED

    # Set the topic status map
    await client.set_topic_join_state(topic, status, message)
