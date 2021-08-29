from unittest.mock import AsyncMock, patch

import pytest

from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import PHXEvent, Topic
from phx_events.utils import make_message


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientSubscribeToRegisteredTopics:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url/')
        self.topic = Topic('topic:subtopic')
        self.phx_client.register_topic_subscription(self.topic)

    async def test_process_topic_registration_responses_task_started(self, mock_websocket_connection):
        mock_process_topic_responses = AsyncMock()
        self.phx_client.process_topic_registration_responses = lambda: mock_process_topic_responses

        with patch.object(self.phx_client, '_loop') as mock_loop:
            await self.phx_client._subscribe_to_registered_topics(mock_websocket_connection)

        mock_loop.create_task.assert_called_with(mock_process_topic_responses)

    async def test_all_topics_in_topic_registration_status_dict_have_messages_sent(self, mock_websocket_connection):
        loop_patch = patch.object(self.phx_client, '_loop')
        gather_patch = patch('phx_events.client.asyncio.gather', new_callable=AsyncMock)
        partial_patch = patch('phx_events.client.partial')

        with loop_patch, partial_patch as mock_partial, gather_patch as mock_gather:
            await self.phx_client._subscribe_to_registered_topics(mock_websocket_connection)

        expected_join_message = make_message(event=PHXEvent.join, topic=self.topic)

        # First partial application applying websocket to _send_message
        mock_partial.assert_called_with(self.phx_client._send_message, mock_websocket_connection)
        # Second partial application applying the messages to the first partial application
        mock_partial.return_value.assert_called_with(expected_join_message)
        # Gather is called on the results of the 2nd partial application
        mock_gather.assert_called_with(mock_partial.return_value.return_value)
