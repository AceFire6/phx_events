import asyncio

import pytest

from phx_events.client import PHXChannelsClient
from phx_events.exceptions import PHXTopicTooManyRegistrationsError
from phx_events.phx_messages import Topic


class TestPHXChannelsClientRegisterTopicSubscription:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url')

    def test_topic_registered_returns_event(self):
        register_event = self.phx_client.register_topic_subscription(Topic('topic:subtopic'))

        assert isinstance(register_event, asyncio.Event)

    def test_registering_the_same_topic_multiple_times_raises_exception(self):
        topic = Topic('topic:subtopic')
        self.phx_client.register_topic_subscription(topic)
        topic_ref = self.phx_client._topic_registration_status[topic].connection_ref

        expected_error = f'Topic {topic} already registered with {topic_ref=}'

        with pytest.raises(PHXTopicTooManyRegistrationsError, match=expected_error):
            self.phx_client.register_topic_subscription(topic)
