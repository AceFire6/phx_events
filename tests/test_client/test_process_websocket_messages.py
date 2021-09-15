import logging

import pytest

from phx_events import json_handler
from phx_events.client import PHXChannelsClient
from phx_events.exceptions import TopicClosedError
from phx_events.phx_messages import Event, PHXEvent, Topic
from phx_events.utils import make_message


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientProcessWebsocketMessages:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url/')
        self.topic = Topic('topic:subtopic')

    async def test_raises_exception_on_phx_close_event(self, mock_websocket_connection):
        close_message = json_handler.dumps(make_message(PHXEvent.close, self.topic))
        mock_websocket_connection.async_iter_values.append(close_message)

        with pytest.raises(TopicClosedError, match=r"'topic:subtopic', 'Upstream closed'"):
            await self.phx_client.process_websocket_messages(mock_websocket_connection)

    async def test_raises_exception_on_phx_error_event(self, mock_websocket_connection):
        error_message = json_handler.dumps(make_message(PHXEvent.error, self.topic))
        mock_websocket_connection.async_iter_values.append(error_message)

        with pytest.raises(TopicClosedError, match=r"'topic:subtopic', 'Upstream error'"):
            await self.phx_client.process_websocket_messages(mock_websocket_connection)

    async def test_puts_message_in_topic_registration_queue_if_appropriate(self, mock_websocket_connection):
        self.phx_client.register_topic_subscription(self.topic)
        topic_registration_message = make_message(PHXEvent.reply, self.topic)
        topic_registration_socket_message = json_handler.dumps(topic_registration_message)
        mock_websocket_connection.async_iter_values.append(topic_registration_socket_message)

        await self.phx_client.process_websocket_messages(mock_websocket_connection)

        queued_registration_message = await self.phx_client._registration_queue.get()

        assert queued_registration_message == topic_registration_message

    async def test_does_not_put_message_in_topic_registration_queue_if_not_phx_reply(self, mock_websocket_connection):
        self.phx_client.register_topic_subscription(self.topic)
        topic_registration_message = make_message(PHXEvent.join, self.topic)
        topic_registration_socket_message = json_handler.dumps(topic_registration_message)
        mock_websocket_connection.async_iter_values.append(topic_registration_socket_message)

        await self.phx_client.process_websocket_messages(mock_websocket_connection)

        assert self.phx_client._registration_queue.empty()

    async def test_does_not_put_message_in_topic_registration_queue_if_registration_event_set(
        self,
        mock_websocket_connection,
    ):
        registration_event = self.phx_client.register_topic_subscription(self.topic)
        topic_registration_message = make_message(PHXEvent.reply, self.topic)
        topic_registration_socket_message = json_handler.dumps(topic_registration_message)
        mock_websocket_connection.async_iter_values.append(topic_registration_socket_message)

        registration_event.set()
        await self.phx_client.process_websocket_messages(mock_websocket_connection)

        assert self.phx_client._registration_queue.empty()

    async def test_event_ignored_if_no_event_handler_registered(self, mock_websocket_connection, caplog):
        # Register a handler for a specific event
        self.phx_client.register_event_handler(Event('specific_event'), handlers=[lambda x, y: None])
        # Create a message about a random_event
        event_socket_message = json_handler.dumps(make_message(Event('random_event'), self.topic))
        mock_websocket_connection.async_iter_values.append(event_socket_message)

        with caplog.at_level(logging.DEBUG):
            await self.phx_client.process_websocket_messages(mock_websocket_connection)

        logger_name, log_level, message = caplog.record_tuples[-1]

        assert logger_name == 'phx_events.async_logger.phx_events.client'
        assert log_level == logging.DEBUG
        assert message == (
            "Ignoring phx_message=PHXMessage(topic='topic:subtopic', ref=None, payload={}, event='random_event') "
            '- no event handlers registered'
        )

    async def test_put_message_in_event_handler_queue_handlers_exist(self, mock_websocket_connection):
        event = Event('specific_event')
        self.phx_client.register_event_handler(event, handlers=[lambda x, y: None])
        event_message = make_message(event, self.topic)
        event_socket_message = json_handler.dumps(event_message)
        mock_websocket_connection.async_iter_values.append(event_socket_message)

        await self.phx_client.process_websocket_messages(mock_websocket_connection)

        event_handler_config = self.phx_client._event_handler_config[event]

        assert event_handler_config.queue.get_nowait() == event_message
