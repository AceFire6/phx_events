import asyncio
from asyncio import AbstractEventLoop, Event, Queue, Task
from concurrent.futures import Executor, ThreadPoolExecutor
from functools import partial
import inspect
from logging import Logger
import signal
from types import TracebackType
from typing import Awaitable, cast, Optional, Type, Union
from urllib.parse import urlencode

import orjson
from websockets import client, exceptions

from phx_events import settings
from phx_events.async_logger import async_logger
from phx_events.exceptions import PHXTopicTooManyRegistrationsError
from phx_events.phx_messages import (
    ChannelEvent,
    ChannelHandlerFunction,
    ChannelMessage,
    CoroutineHandler,
    EventHandlerConfig,
    ExecutorHandler,
    PHXEvent,
    Topic,
)
from phx_events.topic_subscription import SubscriptionStatus, TopicRegistration, TopicSubscribeResult
from phx_events.utils import make_message


class PHXChannelsClient:
    channel_socket_url: str
    logger: Logger

    _client_start_event: Event
    _event_handler_config: dict[ChannelEvent, EventHandlerConfig]
    _topic_registration_status: dict[Topic, TopicRegistration]
    _loop: AbstractEventLoop
    _executor_pool: Optional[Executor]
    _registration_queue: Queue
    _topic_registration_task: Optional[Task]

    def __init__(self, channel_auth_token: Optional[str] = None, event_loop: Optional[AbstractEventLoop] = None):
        self.logger = async_logger.getChild(__name__)
        self.channel_socket_url = settings.PHX_WEBSOCKET_URL
        # Set up auth if it's required
        if channel_auth_token is not None:
            self.channel_socket_url += f'?{urlencode({"token": channel_auth_token})}'

        self._event_handler_config = {}
        self._topic_registration_status = {}
        # Create the Event that will prevent handlers from being run before the client is started
        self._client_start_event = Event()
        self._registration_queue = Queue()
        self._topic_registration_task = None

        self._executor_pool = None
        # Get the default event loop or use the user-provided one if it exists
        self._loop = event_loop or asyncio.get_event_loop()

    async def __aenter__(self) -> 'PHXChannelsClient':
        self.logger.debug('Entering PHXChannelsClient context')
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.logger.debug('Leaving PHXChannelsClient context')
        self.shutdown('Leaving PHXChannelsClient context')

    async def _send_message(self, websocket: client.WebSocketClientProtocol, message: ChannelMessage) -> None:
        self.logger.debug(f'Serialising {message=} to JSON')
        json_message = orjson.dumps(message)

        self.logger.debug(f'Sending {json_message=}')
        await websocket.send(json_message)

    def _parse_message(self, socket_message: Union[str, bytes]) -> ChannelMessage:
        self.logger.debug(f'Got message - {socket_message=}')
        message_dict = orjson.loads(socket_message)

        self.logger.debug(f'Decoding message dict - {message_dict=}')
        return make_message(**message_dict)

    async def _event_processor(self, event: ChannelEvent) -> None:
        """Coroutine used to create tasks that process the given event

        Runs all the handlers in the thread_pool and logs any exceptions.
        """
        # Make all tasks wait until the _client_start_event is set
        # This prevents trying to do any processing until we want the "workers" to start
        await self._client_start_event.wait()

        self.logger.debug(f'{event} Worker - Started!')
        event_handler_config = self._event_handler_config[event]

        # Keep running until we ask all the tasks to stop
        while True:
            # wait until there's a message on the queue to process
            message = await event_handler_config.queue.get()
            self.logger.debug(f'{event} Worker - Got {message=}')

            event_handlers: list[ChannelHandlerFunction] = event_handler_config.default_handlers
            if topic_handlers := event_handler_config.topic_handlers.get(message.topic):
                event_handlers = topic_handlers

            event_tasks = []
            task: Union[Task[None], Awaitable[None]]
            # Run all the event handlers in self.thread_pool managed by AsyncIO or as tasks
            for event_handler in event_handlers:
                if inspect.iscoroutinefunction(event_handler):
                    event_handler = cast(CoroutineHandler, event_handler)
                    task = self._loop.create_task(event_handler(message, self))
                else:
                    event_handler = cast(ExecutorHandler, event_handler)
                    handler_task = partial(event_handler, message, self)
                    task = self._loop.run_in_executor(self._executor_pool, handler_task)

                event_tasks.append(task)

            # Wait until the handlers finish running & await the results to handle errors
            for handler_future in asyncio.as_completed(event_tasks):
                try:
                    await handler_future
                except Exception:
                    self.logger.exception('Error executing handler')

            # Let the queue know the task is done being processed
            event_handler_config.queue.task_done()

    def shutdown(
        self,
        reason: str,
        websocket: Optional[client.WebSocketClientProtocol] = None,
        executor_pool: Optional[Executor] = None,
        wait_for_completion: bool = True,
    ) -> None:
        self.logger.info(f'Event loop shutting down! {reason=}')

        if websocket is not None:
            self._loop.create_task(websocket.close())

        if self._topic_registration_task is not None:
            self._topic_registration_task.cancel()

        for handler_config in self._event_handler_config.values():
            handler_config.task.cancel()

        if executor_pool is not None:
            executor_pool.shutdown(wait=wait_for_completion, cancel_futures=not wait_for_completion)

    def register_event_handler(
        self,
        event: ChannelEvent,
        handlers: list[ChannelHandlerFunction],
        topic: Optional[Topic] = None,
    ) -> None:
        if event not in self._event_handler_config:
            # Create the coroutine that will become a task
            event_coroutine = self._event_processor(event)

            # Create the default EventHandlerConfig
            self._event_handler_config[event] = EventHandlerConfig(
                queue=Queue(),
                default_handlers=[],
                topic_handlers={},
                task=asyncio.create_task(event_coroutine),
            )

        handler_config = self._event_handler_config[event]
        # If there is a topic to be registered for - add the handlers to the topic handler
        if topic is not None:
            handler_config.topic_handlers.setdefault(topic, []).extend(handlers)
        else:
            # otherwise, add them to the default handlers
            handler_config.default_handlers.extend(handlers)

    async def process_topic_registration_responses(self) -> None:
        while True:
            phx_message = await self._registration_queue.get()

            topic = phx_message.topic
            self.logger.info(f'Got topic {topic} join reply {phx_message=}')

            status = SubscriptionStatus.SUCCESS if phx_message.payload['status'] == 'ok' else SubscriptionStatus.FAILED
            status_message = 'SUCCEEDED' if status == SubscriptionStatus.SUCCESS else 'FAILED'
            self.logger.info(f'Topic registration {status_message} - {phx_message=}')

            # Set the topic status map
            topic_registration = self._topic_registration_status[topic]
            # Set topic status with the message
            topic_registration.status = TopicSubscribeResult(status, phx_message)
            # Notify any waiting tasks that the registration has been finalised and the status can be checked
            topic_registration.status_updated_event.set()

    def register_topic_subscription(self, topic: Topic) -> Event:
        if topic_status := self._topic_registration_status.get(topic):
            topic_ref = topic_status.connection_ref
            raise PHXTopicTooManyRegistrationsError(f'Topic {topic} already registered with {topic_ref=}')

        # Create an event to indicate when the reply has been processed
        status_updated_event = Event()

        self._topic_registration_status[topic] = TopicRegistration(status_updated_event=status_updated_event)

        return status_updated_event

    async def process_websocket_messages(self, websocket: client.WebSocketClientProtocol) -> None:
        self.logger.debug('Starting websocket message loop')

        async for socket_message in websocket:
            phx_message = self._parse_message(socket_message)
            self.logger.info(f'Processing message - {phx_message=}')
            event = phx_message.event

            if event == PHXEvent.close:
                self.logger.info(f'Got Phoenix event {event} shutting down - {phx_message=}')
                raise exceptions.ConnectionClosedOK(code=1000, reason='Upstream closed')

            if event == PHXEvent.error:
                # Error happened in Elixir
                self.logger.error(f'Got Phoenix event {event} shutting down - {phx_message=}')
                # Hard exit if the server closes or errors
                raise exceptions.ConnectionClosedError(code=500, reason='Upstream error')

            # Push message into registration queue if appropriate
            if topic_registration_config := self._topic_registration_status.get(phx_message.topic):  # noqa: SIM102
                if event == PHXEvent.reply and not topic_registration_config.status_updated_event.is_set():
                    await self._registration_queue.put(phx_message)

            event_handler_config = self._event_handler_config.get(event)
            if event_handler_config is None:
                self.logger.debug(f'Ignoring {phx_message=} - no event handlers registered')
                continue

            self.logger.info(f'Submitting message to {event=} queue - {phx_message=}')
            await event_handler_config.queue.put(phx_message)

    async def _subscribe_to_registered_topics(self, websocket: client.WebSocketClientProtocol) -> None:
        self._topic_registration_task = self._loop.create_task(self.process_topic_registration_responses())

        registration_messages = []
        for topic, topic_registration_config in self._topic_registration_status.items():
            self.logger.info(f'Creating subscribe message for {topic=}')
            topic_join_message = make_message(event=PHXEvent.join, topic=topic)

            topic_registration_config.connection_ref = topic_join_message.ref
            registration_messages.append(topic_join_message)

        # Send the topic join message
        send_websocket_message = partial(self._send_message, websocket)
        self.logger.info('Sending all topic subscribe messages!')
        await asyncio.gather(*map(send_websocket_message, registration_messages))

    async def start_processing(self, executor_pool: Optional[Executor] = None) -> None:
        if not self._topic_registration_status:
            self.logger.error('No subscribed topics nothing to do here - ending processing!')
            return

        self.logger.debug('Creating the executor pool to use for processing registered handlers')
        self._executor_pool = ThreadPoolExecutor()
        if executor_pool is not None:
            self._executor_pool = executor_pool

        with self._executor_pool as pool:
            self.logger.debug('Connecting to websocket')

            async with client.connect(self.channel_socket_url) as websocket:
                # Close the connection when receiving SIGTERM
                shutdown_handler = partial(
                    self.shutdown,
                    websocket=websocket,
                    executor_pool=pool,
                    wait_for_completion=False,
                )
                self._loop.add_signal_handler(signal.SIGTERM, partial(shutdown_handler, reason='SIGTERM'))
                self._loop.add_signal_handler(signal.SIGINT, partial(shutdown_handler, reason='Keyboard Interrupt'))

                await self._subscribe_to_registered_topics(websocket)

                self._client_start_event.set()
                await self.process_websocket_messages(websocket)
