from phx_events.phx_messages import PHXMessage


class TestSubtopic:
    def test_returns_subtopic_if_it_exists(self):
        phx_message = PHXMessage(topic='topic:subtopic:info', ref='ref', event='test_event', payload={})

        assert phx_message.subtopic == 'subtopic:info'

    def test_returns_none_if_it_does_not_exist(self):
        phx_message = PHXMessage(topic='topic', ref='ref', event='test_event', payload={})

        assert phx_message.subtopic is None
