import asyncio
from unittest.mock import Mock, patch

from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import Event, Topic


async def handler_function(message, client):
    return None


class TestPHXChannelsClientRegisterEventHandler:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url/')
        self.event = Event('event_name')

    def test_event_added_to_event_handler_config(self):
        mock_coroutine = Mock()
        mock_event_processor = Mock(return_value=mock_coroutine)
        self.phx_client._event_processor = mock_event_processor

        with patch.object(self.phx_client, '_loop') as mock_loop:
            self.phx_client.register_event_handler(event=self.event, handlers=[handler_function])

        handler_config = self.phx_client._event_handler_config[self.event]
        # _event_process is called with passed in event
        mock_event_processor.assert_called_with(self.event)
        # _loop.create_task is called with mock_coroutine the result of mock_event_processor(self.event)
        mock_loop.create_task.assert_called_with(mock_coroutine)

        assert isinstance(handler_config.queue, asyncio.Queue)
        # Assert that the task is the result of calling _loop.create_task
        assert handler_config.task == mock_loop.create_task.return_value
        assert handler_config.default_handlers == [handler_function]
        assert handler_config.topic_handlers == {}

    def test_handlers_add_to_topic_handlers_if_topic_is_passed_in(self):
        topic = Topic('topic:subtopic')

        with patch.object(self.phx_client, '_loop'):
            self.phx_client.register_event_handler(
                event=self.event,
                handlers=[handler_function],
                topic=topic,
            )

        handler_config = self.phx_client._event_handler_config[self.event]

        assert len(handler_config.default_handlers) == 0
        assert handler_config.topic_handlers == {topic: [handler_function]}

    def test_events_with_the_same_name_are_grouped(self):
        def second_handler_function(message, client):
            return None

        topic = Topic('topic:subtopic')

        with patch.object(self.phx_client, '_loop'):
            self.phx_client.register_event_handler(event=self.event, handlers=[handler_function])
            self.phx_client.register_event_handler(event=self.event, handlers=[second_handler_function])
            self.phx_client.register_event_handler(event=self.event, handlers=[second_handler_function], topic=topic)

        handler_config = self.phx_client._event_handler_config[self.event]

        assert len(handler_config.default_handlers) == 2
        assert handler_function in handler_config.default_handlers
        assert second_handler_function in handler_config.default_handlers
        assert len(handler_config.topic_handlers) == 1
        assert handler_config.topic_handlers == {topic: [second_handler_function]}
