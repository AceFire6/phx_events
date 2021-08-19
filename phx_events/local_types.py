from typing import NewType, Union

from phx_events.phx_messages import PHXEvent, PHXEventMessage, PHXMessage


RawEvent = NewType('RawEvent', str)
ChannelEvent = Union[PHXEvent, RawEvent]
ChannelMessage = Union[PHXMessage, PHXEventMessage]
