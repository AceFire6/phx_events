import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from unittest.mock import Mock

import pytest

from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import ChannelMessage, Event, Topic
from phx_events.utils import make_message


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientEventProcessor:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url/')
        self.event = Event('event_name')
        self.other_event = Event('other_event_name')
        self.topic = Topic('topic:subtopic')

        self.event_handler_event = asyncio.Event()
        self.other_event_handler_event = asyncio.Event()
        self.event_topic_handler_event = asyncio.Event()

        async def event_handler(message: ChannelMessage, client: PHXChannelsClient) -> None:
            client.logger.info(f'{event_handler.__name__} {message=}')
            self.event_handler_event.set()

        async def other_event_handler(message: ChannelMessage, client: PHXChannelsClient) -> None:
            client.logger.info(f'{other_event_handler.__name__} {message=}')
            self.other_event_handler_event.set()

        def event_topic_handler(message: ChannelMessage, client: PHXChannelsClient) -> None:
            client.logger.info(f'{event_topic_handler.__name__} {message=}')
            self.event_topic_handler_event.set()

        self.event_handler = event_handler
        self.other_event_handler = other_event_handler
        self.event_topic_handler = event_topic_handler
        # Register the first event handler
        self.phx_client.register_event_handler(self.event, handlers=[event_handler])
        # Register the second event handler
        self.phx_client.register_event_handler(self.other_event, handlers=[other_event_handler])
        # and topic event handler
        self.phx_client.register_event_handler(self.event, handlers=[event_topic_handler], topic=self.topic)

        # Cancel all the tasks started during registration
        for event_handler_config in self.phx_client._event_handler_config.values():
            event_handler_config.task.cancel()

        # Set the client start event so the task doesn't wait in any of the tests
        self.phx_client._client_start_event.set()

    async def test_waits_on_client_start_event(self, caplog):
        self.phx_client._client_start_event.clear()

        with pytest.raises(asyncio.TimeoutError), caplog.at_level(logging.DEBUG):
            await asyncio.wait_for(self.phx_client._event_processor(self.event), timeout=0.2)

        _, log_level, message = caplog.record_tuples[0]

        assert len(caplog.record_tuples) == 1
        assert log_level == logging.DEBUG
        assert message == f'{self.event} Worker - Waiting for client start!'

    async def test_only_event_handlers_used_for_event_no_topic(self, event_loop, caplog):
        event_handler_config = self.phx_client._event_handler_config[self.event]
        event_message = make_message(self.event, Topic('random_topic'))
        await event_handler_config.queue.put(event_message)

        mock_loop = Mock(event_loop, autospec=True, wraps=event_loop)
        self.phx_client._loop = mock_loop

        # Set log level
        caplog.set_level(logging.INFO)
        event_loop.create_task(self.phx_client._event_processor(self.event))

        # Wait for task to process messages
        await event_handler_config.queue.join()

        assert event_handler_config.queue.empty()
        # The event handler is called with the message and client
        assert self.event_handler_event.is_set()
        assert caplog.messages[0] == f'{self.event_handler.__name__} message={event_message}'
        # We only expect the coroutine to have been called
        mock_loop.create_task.assert_called()
        # We don't expect the event_topic_handler to have been called
        mock_loop.run_in_executor.assert_not_called()

    async def test_all_event_handlers_used_for_event_with_topic(self, event_loop, caplog):
        event_handler_config = self.phx_client._event_handler_config[self.event]
        event_message = make_message(self.event, self.topic)
        await event_handler_config.queue.put(event_message)

        mock_loop = Mock(event_loop, wraps=event_loop)
        self.phx_client._loop = mock_loop
        self.phx_client._executor_pool = ThreadPoolExecutor()

        caplog.set_level(logging.INFO)
        event_loop.create_task(self.phx_client._event_processor(self.event))

        # Wait for task to process messages
        await event_handler_config.queue.join()

        assert event_handler_config.queue.empty()
        # The event handler is called with the message and client
        assert self.event_handler_event.is_set()
        assert self.event_topic_handler_event.is_set()
        assert len(caplog.messages) == 2
        assert f'{self.event_handler.__name__} message={event_message}' in caplog.messages
        assert f'{self.event_topic_handler.__name__} message={event_message}' in caplog.messages
        # We only expect the coroutine to have been called
        mock_loop.create_task.assert_called()
        # We don't expect the event_topic_handler to have been called
        mock_loop.run_in_executor.assert_called()

    async def test_event_handler_errors_intercepted_and_logged(self, event_loop, caplog):
        async def coro_erroring_event_handler(message, client):
            raise Exception(coro_erroring_event_handler.__name__)

        def erroring_event_handler(message, client):
            raise Exception(erroring_event_handler.__name__)

        event = Event('new_event')
        self.phx_client.register_event_handler(
            event,
            handlers=[erroring_event_handler, coro_erroring_event_handler],
        )
        event_handler_config = self.phx_client._event_handler_config[event]
        event_handler_config.task.cancel()

        event_message = make_message(event, self.topic)
        await event_handler_config.queue.put(event_message)

        mock_loop = Mock(event_loop, wraps=event_loop)
        self.phx_client._loop = mock_loop
        self.phx_client._executor_pool = ThreadPoolExecutor()

        caplog.set_level(logging.INFO)
        event_loop.create_task(self.phx_client._event_processor(event))

        # Wait for task to process messages
        await event_handler_config.queue.join()
        expected_exception_logs = [
            f"Error executing handler - exception=Exception('{erroring_event_handler.__name__}')",
            f"Error executing handler - exception=Exception('{coro_erroring_event_handler.__name__}')",
        ]

        assert event_handler_config.queue.empty()
        assert len(caplog.messages) == 2
        assert all(error_log in caplog.messages for error_log in expected_exception_logs)
        # We only expect the coroutine to have been called
        mock_loop.create_task.assert_called()
        # We don't expect the event_topic_handler to have been called
        mock_loop.run_in_executor.assert_called()
