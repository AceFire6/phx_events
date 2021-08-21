from phx_events.phx_messages import Event, PHXMessage, Topic


class TestSubtopic:
    def test_returns_subtopic_if_it_exists(self):
        phx_message = PHXMessage(topic=Topic('topic:subtopic:info'), ref='ref', event=Event('test_event'), payload={})

        assert phx_message.subtopic == 'subtopic:info'

    def test_returns_none_if_it_does_not_exist(self):
        phx_message = PHXMessage(topic=Topic('topic'), ref='ref', event=Event('test_event'), payload={})

        assert phx_message.subtopic is None
