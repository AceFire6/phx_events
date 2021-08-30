from unittest.mock import AsyncMock

from hypothesis import given
import pytest

from phx_events import json_handler
from phx_events.client import PHXChannelsClient
from phx_events.utils import make_message
from tests.strategy_utils import channel_event_strategy


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientSendMessage:
    @given(channel_event_strategy())
    async def test_correct_message_passed_to_websocket_send(self, event_dict):
        mock_websocket = AsyncMock()
        message = make_message(**event_dict)

        async with PHXChannelsClient('ws://test.websocket/') as client:
            await client._send_message(mock_websocket, message)

        mock_websocket.send.assert_called_with(json_handler.dumps(message))
        mock_websocket.send.assert_awaited()
