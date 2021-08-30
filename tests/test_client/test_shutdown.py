from asyncio import Queue
from unittest.mock import AsyncMock, Mock

from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import EventHandlerConfig


class TestPHXChannelsClientShutdown:
    def setup(self):
        self.event_loop = AsyncMock()
        self.phx_client = PHXChannelsClient('ws://url', event_loop=self.event_loop)

    def test_if_websocket_is_not_none_close_task_queued(self):
        close_coroutine = Mock()
        websocket = Mock()
        websocket.close.return_value = close_coroutine

        self.phx_client.shutdown('test', websocket=websocket)

        websocket.close.assert_called()
        self.event_loop.create_task.assert_called_with(close_coroutine)

    def test_if_topic_registration_task_is_not_none_cancel_task(self):
        topic_registration_task = Mock()
        self.phx_client._topic_registration_task = topic_registration_task

        self.phx_client.shutdown('test')

        topic_registration_task.cancel.assert_called()

    def test_any_event_handlers_registered_tasks_are_cancelled(self):
        event_handler_1_task = Mock()
        event_handler_2_task = Mock()

        self.phx_client._event_handler_config = {
            'event_1_name': EventHandlerConfig(
                queue=Queue(),
                default_handlers=[],
                topic_handlers={},
                task=event_handler_1_task,
            ),
            'event_2_name': EventHandlerConfig(
                queue=Queue(),
                default_handlers=[],
                topic_handlers={},
                task=event_handler_2_task,
            ),
        }

        self.phx_client.shutdown('test')

        event_handler_1_task.cancel.assert_called()
        event_handler_2_task.cancel.assert_called()

    def test_if_executor_pool_is_not_none_call_shutdown(self):
        executor_pool = Mock()

        self.phx_client.shutdown('test', executor_pool=executor_pool)

        executor_pool.shutdown.assert_called_with(wait=True, cancel_futures=False)

    def test_if_executor_pool_is_not_none_call_shutdown_with_no_wait(self):
        executor_pool = Mock()

        self.phx_client.shutdown('test', executor_pool=executor_pool, wait_for_completion=False)

        executor_pool.shutdown.assert_called_with(wait=False, cancel_futures=True)
