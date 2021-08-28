import asyncio
from urllib.parse import urlencode

import pytest

from phx_events.client import PHXChannelsClient


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientInit:
    def setup(self):
        self.socket_url = 'ws://test.socket/url/'
        self.channel_auth_token = 'test_token'

        self.phx_channels_client = PHXChannelsClient(self.socket_url, self.channel_auth_token)

    def test_async_logger_child_set_as_logger_on_client(self):
        from phx_events.async_logger import async_logger

        assert self.phx_channels_client.logger.parent == async_logger

    def test_channel_socket_url_has_token_if_specified(self):
        no_token_client = PHXChannelsClient(self.socket_url)

        assert no_token_client.channel_socket_url == self.socket_url
        assert self.phx_channels_client.channel_socket_url == f'{self.socket_url}?token={self.channel_auth_token}'

    def test_channel_socket_url_token_is_made_url_safe(self):
        unsafe_token = '==??=='
        safe_token_client = PHXChannelsClient(self.socket_url, channel_auth_token=unsafe_token)

        assert safe_token_client.channel_socket_url != f'{self.socket_url}?token={unsafe_token}'
        assert safe_token_client.channel_socket_url == f'{self.socket_url}?{urlencode({"token": unsafe_token})}'

    def test_event_loop_set_by_default_if_not_specified(self):
        no_loop_specified_client = PHXChannelsClient(self.socket_url)

        assert isinstance(no_loop_specified_client._loop, asyncio.BaseEventLoop)

    def test_event_loop_set_to_argument_if_specified(self):
        event_loop = asyncio.get_event_loop()
        specified_loop_client = PHXChannelsClient(self.socket_url, event_loop=event_loop)

        assert specified_loop_client._loop == event_loop
