from unittest.mock import patch

import pytest

from phx_events.client import PHXChannelsClient


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientAEnter:
    async def test_returns_self_when_using_as_with_context_manager(self):
        phx_client = PHXChannelsClient('ws://web.socket/url/')

        async with phx_client as test_phx_client:
            assert isinstance(test_phx_client, PHXChannelsClient)
            assert phx_client == test_phx_client


class TestPHXChannelsClientAExit:
    async def test_calls_shutdown_with_correct_reason(self):
        phx_client = PHXChannelsClient('ws://web.socket/url/')

        with patch.object(phx_client, 'shutdown') as mock_shutdown:
            await phx_client.__aexit__()

        mock_shutdown.assert_called_with('Leaving PHXChannelsClient context')
