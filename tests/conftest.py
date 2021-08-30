from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# If this is removed then remove the additional options in
# the pytest.ini file
pytest_plugins = ['hypothesis.extra.pytestplugin']


class MockWebsocketConnection(AsyncMock):
    async_iter_values: list[Any]

    def __aiter__(self) -> Any:
        pass


@pytest.fixture()
def mock_websocket_client() -> MagicMock:  # type: ignore[misc]
    with patch('phx_events.client.client', autospec=True) as mocked_websocket:
        yield mocked_websocket


@pytest.fixture()
async def mock_websocket_connection(mock_websocket_client) -> MockWebsocketConnection:  # type: ignore[misc]
    async def async_iter(self) -> AsyncIterator[Any]:
        for item in self.async_iter_values:  # noqa: SIM104
            yield item

    async with mock_websocket_client.connect('ws://test') as client_connection:
        # Create an async iterator that loops through set values
        client_connection.async_iter_values = []
        client_connection.__aiter__ = async_iter

        yield client_connection


@pytest.fixture()
def mock_executor_pool() -> MagicMock:  # type: ignore[misc]
    from concurrent.futures import ThreadPoolExecutor

    mock_executor = MagicMock(ThreadPoolExecutor, autospec=True)
    yield mock_executor


@pytest.fixture()
def mock_executor_contextmanager(mock_executor_pool) -> MagicMock:  # type: ignore[misc]
    with mock_executor_pool as mock_pool:
        yield mock_pool
