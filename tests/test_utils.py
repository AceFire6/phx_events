from freezegun import freeze_time
from hypothesis import given, strategies as st

from phx_events import utils
from phx_events.phx_messages import Event, PHXEvent, PHXEventMessage, PHXMessage
from tests.strategy_utils import channel_event_strategy, event_strategy, phx_event_strategy, PHX_EVENTS


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
    @given(phx_event_strategy())
    def test_phx_event_message_returned_for_phx_event(self, phx_event_dict):
        message = utils.make_message(
            event=phx_event_dict['event'],
            topic=phx_event_dict['topic'],
            ref=phx_event_dict['ref'],
            payload=phx_event_dict['payload'],
        )

        assert isinstance(message, PHXEventMessage)
        assert message.event == PHXEvent(phx_event_dict['event'])

    @given(event_strategy())
    def test_phx_message_returned_for_other_events(self, event_dict):
        message = utils.make_message(
            event=event_dict['event'],
            topic=event_dict['topic'],
            ref=event_dict['ref'],
            payload=event_dict['payload'],
        )

        assert isinstance(message, PHXMessage)
        assert isinstance(message.event, str)

    @given(channel_event_strategy(payload=st.none()))
    def test_none_payload_turned_into_empty_dict(self, event_dict):
        message = utils.make_message(
            event=event_dict['event'],
            topic=event_dict['topic'],
            ref=event_dict['ref'],
            payload=event_dict['payload'],
        )

        assert message.payload == {}


class TestGenerateReference:
    @given(st.text() | st.sampled_from(PHXEvent))
    def test_returns_correctly_for_event(self, event):
        frozen_time = '2021-08-20T15:58:34'

        with freeze_time(frozen_time):
            ref = utils.generate_reference(event)

        assert ref == f'20210820155834:{event!s}'
