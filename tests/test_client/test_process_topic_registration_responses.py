import pytest

from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import PHXEvent, Topic
from phx_events.topic_subscription import SubscriptionStatus
from phx_events.utils import make_message


pytestmark = pytest.mark.asyncio


class TestPHXChannelsClientProcessTopicRegistrationResponses:
    def setup(self):
        self.phx_client = PHXChannelsClient('ws://url/')
        self.topic = Topic('topic:subtopic')
        self.topic_event = self.phx_client.register_topic_subscription(self.topic)

    async def test_updates_registration_status_for_success(self, event_loop):
        registration_response = make_message(PHXEvent.reply, self.topic, payload={'status': 'ok'})
        await self.phx_client._registration_queue.put(registration_response)

        event_loop.create_task(self.phx_client.process_topic_registration_responses())

        # Wait until the item is processed
        await self.phx_client._registration_queue.join()
        registration_status = self.phx_client._topic_registration_status[self.topic]

        assert self.topic_event.is_set()
        assert registration_status.result.status == SubscriptionStatus.SUCCESS
        assert registration_status.result.result_message == registration_response

    async def test_updates_registration_status_for_failed(self, event_loop):
        negative_registration_response = make_message(PHXEvent.reply, self.topic, payload={'status': 'error'})
        await self.phx_client._registration_queue.put(negative_registration_response)

        event_loop.create_task(self.phx_client.process_topic_registration_responses())

        # Wait until the item is processed
        await self.phx_client._registration_queue.join()
        registration_status = self.phx_client._topic_registration_status[self.topic]

        assert self.topic_event.is_set()
        assert registration_status.result.status == SubscriptionStatus.FAILED
        assert registration_status.result.result_message == negative_registration_response
