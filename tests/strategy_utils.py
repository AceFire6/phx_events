from typing import Any, Optional, TypedDict

from hypothesis import strategies as st
from hypothesis.strategies import composite, DrawFn, SearchStrategy


PHX_EVENTS = ['phx_close', 'phx_error', 'phx_join', 'phx_reply', 'phx_leave']

safe_float_strategy = st.floats(allow_nan=False, allow_infinity=False)
safe_decimal_strategy = st.decimals(allow_nan=False, allow_infinity=False)
# These are the min and max values for a 64bit integer - orjson can't handle bigger ints
# See here: https://github.com/ijl/orjson#int
safe_int_strategy = st.integers(min_value=-9223372036854775807, max_value=18446744073709551615)

message_payload = st.dictionaries(
    keys=st.text(),
    values=st.text() | st.booleans() | safe_float_strategy | safe_int_strategy | safe_decimal_strategy | st.datetimes(),
)


class EventDict(TypedDict):
    topic: str
    event: str
    ref: Optional[str]
    payload: Optional[dict[str, Any]]


@composite
def channel_event_strategy(
    draw: DrawFn,
    topic: Optional[SearchStrategy[str]] = None,
    event: Optional[SearchStrategy[str]] = None,
    ref: Optional[SearchStrategy[str]] = None,
    payload: Optional[SearchStrategy[Optional[dict[str, Any]]]] = None,
) -> EventDict:
    if topic is None:
        topic = st.text()

    if event is None:
        event = st.sampled_from(PHX_EVENTS) | st.text()

    if ref is None:
        ref = st.text() | st.none()  # type: ignore[operator]

    if payload is None:
        payload = st.none() | message_payload

    return {
        'topic': draw(topic),
        'event': draw(event),
        'ref': draw(ref),
        'payload': draw(payload),
    }


def phx_event_strategy(
    topic: Optional[SearchStrategy[str]] = None,
    event: Optional[SearchStrategy[str]] = None,
    ref: Optional[SearchStrategy[str]] = None,
    payload: Optional[SearchStrategy[Optional[dict[str, Any]]]] = None,
) -> SearchStrategy[EventDict]:
    if event is None:
        event = st.sampled_from(PHX_EVENTS)

    return channel_event_strategy(topic, event, ref, payload)


def event_strategy(
    topic: Optional[SearchStrategy[str]] = None,
    event: Optional[SearchStrategy[str]] = None,
    ref: Optional[SearchStrategy[str]] = None,
    payload: Optional[SearchStrategy[Optional[dict[str, Any]]]] = None,
) -> SearchStrategy[EventDict]:
    if event is None:
        event = st.text()

    return channel_event_strategy(topic, event, ref, payload)
