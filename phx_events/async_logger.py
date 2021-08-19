import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import SimpleQueue


class LocalQueueHandler(QueueHandler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.enqueue(record)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.handleError(record)


def setup_queue_logging() -> tuple[logging.Logger, QueueListener]:
    """Move log handlers to a separate thread.

    Replace handlers on the root logger with a LocalQueueHandler,
    and start a logging.QueueListener holding the original
    handlers.
    """
    queue: SimpleQueue = SimpleQueue()
    queue_logger = logging.getLogger(__name__)

    handlers: list[logging.Handler] = []
    # Last resort handler if no logging is configured
    if logging.lastResort is not None:
        handlers.append(logging.lastResort)

    local_queue_handler = LocalQueueHandler(queue)
    queue_logger.addHandler(local_queue_handler)

    for handler in queue_logger.handlers:
        if handler is not local_queue_handler:
            queue_logger.removeHandler(handler)
            handlers.append(handler)

    listener = QueueListener(queue, *handlers, respect_handler_level=True)
    listener.start()

    return queue_logger, listener


async_logger, queue_listener = setup_queue_logging()
