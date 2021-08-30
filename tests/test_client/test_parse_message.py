from hypothesis import given

from phx_events import json_handler
from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import PHXEvent, PHXEventMessage, PHXMessage
from tests.strategy_utils import event_strategy, phx_event_strategy


class TestPHXChannelsClientParseMessage:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url')

    @given(event_strategy())
    def test_returns_phx_message_for_event_socket_message(self, event_dict):
        socket_message = json_handler.dumps(event_dict)
        # This is done to convert any Python types in the event_dict payload to JSON-versions
        reserialised_event_dict = json_handler.loads(socket_message)

        parsed_message = self.phx_client._parse_message(socket_message)

        assert isinstance(parsed_message, PHXMessage)
        assert parsed_message.topic == reserialised_event_dict['topic'] == event_dict['topic']
        assert parsed_message.event == reserialised_event_dict['event'] == event_dict['event']
        assert parsed_message.ref == reserialised_event_dict['ref'] == event_dict['ref']
        assert parsed_message.payload == (reserialised_event_dict['payload'] or {})

    @given(phx_event_strategy())
    def test_returns_phx_event_message_for_event_socket_message(self, event_dict):
        socket_message = json_handler.dumps(event_dict)
        # This is done to convert any Python types in the event_dict payload to JSON-versions
        reserialised_event_dict = json_handler.loads(socket_message)

        parsed_message = self.phx_client._parse_message(socket_message)

        assert isinstance(parsed_message, PHXEventMessage)
        assert parsed_message.topic == reserialised_event_dict['topic'] == event_dict['topic']
        assert parsed_message.event == PHXEvent(reserialised_event_dict['event']) == PHXEvent(event_dict['event'])
        assert parsed_message.ref == reserialised_event_dict['ref'] == event_dict['ref']
        assert parsed_message.payload == (reserialised_event_dict['payload'] or {})
