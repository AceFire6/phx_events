from datetime import datetime
from typing import Any, Optional

from phx_events.phx_messages import ChannelEvent, ChannelMessage, PHXEvent, PHXEventMessage, PHXMessage, Topic


def parse_event(event: ChannelEvent) -> ChannelEvent:
    try:
        return PHXEvent(event)
    except ValueError:
        return event


def make_message(
    event: ChannelEvent,
    topic: Topic,
    ref: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> ChannelMessage:
    if payload is None:
        payload = {}

    processed_event = parse_event(event)
    if isinstance(processed_event, PHXEvent):
        return PHXEventMessage(event=processed_event, topic=topic, ref=ref, payload=payload)
    else:
        return PHXMessage(event=processed_event, topic=topic, ref=ref, payload=payload)


def generate_reference(event: ChannelEvent) -> str:
    return f'{datetime.now():%Y%m%d%H%M%S}:{event}'
