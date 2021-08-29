import signal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import Topic


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientStartProcessing:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url/')
        self.phx_client.register_topic_subscription(Topic('topic:subtopic'))

    async def test_does_nothing_if_no_topics_registered(self, caplog):
        await PHXChannelsClient('ws://url/').start_processing()

        assert len(caplog.messages) == 1
        assert caplog.messages[0] == 'No subscribed topics nothing to do here - ending processing!'

    async def test_threadpool_executor_used_if_no_executor_pool_specified(self, mock_websocket_client):
        with patch('phx_events.client.ThreadPoolExecutor') as mock_thread_pool:
            await self.phx_client.start_processing()

        mock_thread_pool.assert_called()

    async def test_websocket_client_called_with_url(self, mock_websocket_client):
        await self.phx_client.start_processing()

        mock_websocket_client.connect.assert_called_with(self.phx_client.channel_socket_url)

    async def test_signal_handlers_functions_created_and_registered_correctly(
        self,
        mock_executor_pool,
        mock_executor_contextmanager,
        mock_websocket_connection,
    ):
        mock_loop = Mock()
        self.phx_client._loop = mock_loop
        # Prevent any processing attempts
        self.phx_client._subscribe_to_registered_topics = AsyncMock()
        self.phx_client.process_websocket_messages = AsyncMock()

        partial_patch = patch('phx_events.client.partial')
        shutdown_patch = patch.object(self.phx_client, 'shutdown')

        with shutdown_patch as mock_shutdown, partial_patch as mock_partial:
            await self.phx_client.start_processing(executor_pool=mock_executor_pool)

        mock_partial.assert_any_call(
            mock_shutdown,
            websocket=mock_websocket_connection,
            executor_pool=mock_executor_contextmanager,
            wait_for_completion=False,
        )
        mock_partial.assert_any_call(mock_partial.return_value, reason='SIGTERM')
        mock_partial.assert_any_call(mock_partial.return_value, reason='Keyboard Interrupt')
        mock_loop.add_signal_handler.assert_any_call(signal.SIGTERM, mock_partial.return_value)
        mock_loop.add_signal_handler.assert_any_call(signal.SIGINT, mock_partial.return_value)

    async def test_subscribe_to_registered_topics_called_with_websocket(self, mock_websocket_connection):
        # Prevent any processing attempts
        self.phx_client.process_websocket_messages = AsyncMock()

        mock_subscribe_to_topics = AsyncMock()
        self.phx_client._subscribe_to_registered_topics = mock_subscribe_to_topics

        await self.phx_client.start_processing()

        mock_subscribe_to_topics.assert_called_with(mock_websocket_connection)

    async def test_process_websocket_messages_called_with_websocket(self, mock_websocket_connection):
        # Prevent any processing attempts
        self.phx_client._subscribe_to_registered_topics = AsyncMock()

        mock_process_websocket_messages = AsyncMock()
        self.phx_client.process_websocket_messages = mock_process_websocket_messages

        await self.phx_client.start_processing()

        mock_process_websocket_messages.assert_called_with(mock_websocket_connection)
