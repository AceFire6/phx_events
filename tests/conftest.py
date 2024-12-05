from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# If this is removed then remove the additional options in
# the pytest.ini file
pytest_plugins = ['hypothesis.extra.pytestplugin']


@pytest.fixture()
def mock_websocket_connect() -> MagicMock:  # type: ignore[misc]
    with patch('phx_events.client.ws_connect', autospec=True) as mocked_websocket_connect:
        yield mocked_websocket_connect


@pytest.fixture()
async def mock_websocket_connection(mock_websocket_connect) -> AsyncMock:  # type: ignore[misc]
    async with mock_websocket_connect('ws://test') as client_connection:
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
