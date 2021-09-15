from phx_events.phx_messages import Topic


class PHXClientError(Exception):
    pass


class PHXTopicTooManyRegistrationsError(PHXClientError):
    pass


class TopicClosedError(PHXClientError):
    def __init__(self, topic: Topic, reason: str):
        self.topic = topic
        self.reason = reason
        super().__init__(topic, reason)
