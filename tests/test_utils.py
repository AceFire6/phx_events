from freezegun import freeze_time
from hypothesis import given, strategies as st

from phx_events import utils
from phx_events.phx_messages import Event, PHXEvent, PHXEventMessage, PHXMessage


PHX_EVENTS = ['phx_close', 'phx_error', 'phx_join', 'phx_reply', 'phx_leave']
message_payload = st.dictionaries(
    keys=st.text(),
    values=st.text() | st.booleans() | st.floats() | st.integers() | st.decimals() | st.datetimes(),
)


class TestParseEvent:
    @given(st.sampled_from(PHX_EVENTS))
    def test_returns_event_enum_for_valid_phx_events(self, event_name):
        parsed_event = utils.parse_event(Event(event_name))

        assert isinstance(parsed_event, PHXEvent)

    @given(st.text().filter(lambda x: x not in PHX_EVENTS))
    def test_returns_string_for_anything_that_is_not_a_phx_event(self, random_event):
        parsed_event = utils.parse_event(Event(random_event))

        assert isinstance(parsed_event, str)


class TestMakeMessage:
    @given(
        event=st.sampled_from(PHX_EVENTS),
        topic=st.text(),
        ref=st.text() | st.none(),
        payload=message_payload,
    )
    def test_phx_event_message_returned_for_phx_event(self, event, topic, ref, payload):
        message = utils.make_message(
            event=event,
            topic=topic,
            ref=ref,
            payload=payload,
        )

        assert isinstance(message, PHXEventMessage)
        assert message.event == PHXEvent(event)

    @given(
        event=st.text().filter(lambda x: x not in PHX_EVENTS),
        topic=st.text(),
        ref=st.text() | st.none(),
        payload=message_payload,
    )
    def test_phx_message_returned_for_other_events(self, event, topic, ref, payload):
        message = utils.make_message(
            event=event,
            topic=topic,
            ref=ref,
            payload=payload,
        )

        assert isinstance(message, PHXMessage)
        assert isinstance(message.event, str)

    @given(
        event=st.text(),
        topic=st.text(),
        ref=st.text() | st.none(),
        payload=st.none(),
    )
    def test_none_payload_turned_into_empty_dict(self, event, topic, ref, payload):
        message = utils.make_message(
            event=event,
            topic=topic,
            ref=ref,
            payload=payload,
        )

        assert message.payload == {}


class TestGenerateReference:
    @given(st.text() | st.sampled_from(PHXEvent))
    def test_returns_correctly_for_event(self, event):
        frozen_time = '2021-08-20T15:58:34'

        with freeze_time(frozen_time):
            ref = utils.generate_reference(event)

        assert ref == f'20210820155834:{event!s}'
