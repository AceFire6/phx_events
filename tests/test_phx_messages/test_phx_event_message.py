from phx_events.phx_messages import PHXEvent, PHXEventMessage, Topic


class TestSubtopic:
    def test_returns_subtopic_if_it_exists(self):
        phx_message = PHXEventMessage(topic=Topic('topic:subtopic:info'), ref='ref', event=PHXEvent.reply, payload={})

        assert phx_message.subtopic == 'subtopic:info'

    def test_returns_none_if_it_does_not_exist(self):
        phx_message = PHXEventMessage(topic=Topic('topic'), ref='ref', event=PHXEvent.reply, payload={})

        assert phx_message.subtopic is None
