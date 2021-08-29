# If this is removed then remove the additional options in
# the pytest.ini file
from unittest.mock import patch

import pytest


pytest_plugins = ['hypothesis.extra.pytestplugin']


@pytest.fixture()
def mock_websocket_client():
    with patch('phx_events.client.client', autospec=True) as mocked_websocket:
        yield mocked_websocket
