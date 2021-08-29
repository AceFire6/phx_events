# If this is removed then remove the additional options in
# the pytest.ini file
from unittest.mock import MagicMock, patch

import pytest


pytest_plugins = ['hypothesis.extra.pytestplugin']


@pytest.fixture()
def mock_websocket_client():
    with patch('phx_events.client.client', autospec=True) as mocked_websocket:
        yield mocked_websocket


@pytest.fixture()
async def mock_websocket_connection(mock_websocket_client):
    async with mock_websocket_client.connect('ws://test') as client_connection:
        yield client_connection


@pytest.fixture()
def mock_executor_pool():
    from concurrent.futures import ThreadPoolExecutor

    mock_executor = MagicMock(ThreadPoolExecutor, autospec=True)
    yield mock_executor


@pytest.fixture()
def mock_executor_contextmanager(mock_executor_pool):
    with mock_executor_pool as mock_pool:
        yield mock_pool
