from datetime import datetime
from typing import Any, Optional

from phx_events.local_types import ChannelEvent, ChannelMessage
from phx_events.phx_messages import PHXEvent, PHXEventMessage, PHXMessage


def parse_event(raw_event: ChannelEvent) -> ChannelEvent:
    try:
        return PHXEvent(raw_event)
    except ValueError:
        return raw_event


def make_message(
    event: ChannelEvent,
    topic: str,
    reference: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> ChannelMessage:
    if payload is None:
        payload = {}

    processed_event = parse_event(event)
    if isinstance(processed_event, PHXEvent):
        return PHXEventMessage(event=processed_event, topic=topic, ref=reference, payload=payload)
    else:
        return PHXMessage(event=processed_event, topic=topic, ref=reference, payload=payload)


def generate_reference(event: ChannelEvent) -> str:
    return f'{datetime.now():%Y%m%d%H%M%S}:{event}'
