# PHX Events

[![Test PHX Events](https://github.com/AceFire6/phx_events/actions/workflows/run_tests.yml/badge.svg)](https://github.com/AceFire6/phx_events/actions/workflows/run_tests.yml)
[![Lint Python](https://github.com/AceFire6/phx_events/actions/workflows/lint_python.yml/badge.svg)](https://github.com/AceFire6/phx_events/actions/workflows/lint_python.yml)
[![Lint Github Workflows](https://github.com/AceFire6/phx_events/actions/workflows/lint_workflows.yml/badge.svg)](https://github.com/AceFire6/phx_events/actions/workflows/lint_workflows.yml)

PHX Events is an AsyncIO library to set up a websocket connection with 
[Phoenix Channels](https://phoenixframework.readme.io/docs/channels) in Python 3.9+.

## Installing PHX Events

### From Pip
```shell
pip install phx-events
```

### From Source
Clone the Git repo and then install the dependencies
```shell
pip install -r requirements/core.txt
```

## Use the client in your code:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

from phx_events.client import PHXChannelsClient
from phx_events.phx_messages import ChannelMessage, Event, Topic


def print_handler(message: ChannelMessage, client: PHXChannelsClient) -> None:
    client.logger.info(f'DEFAULT: {message=}')


async def async_print_handler(message: ChannelMessage, client: PHXChannelsClient) -> None:
    client.logger.info(f'ASYNC: {message=}')


async def main() -> None:
    token = 'auth_token'
    client: PHXChannelsClient

    with ThreadPoolExecutor() as pool:
        async with PHXChannelsClient(token) as client:
            client.register_event_handler(
                event=Event('event_name'),
                handlers=[
                    print_handler,
                    async_print_handler,
                ],
            )
            client.register_topic_subscription(Topic('topic:subtopic'))

            await client.start_processing(pool)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
```

## Developing

This project uses [`pip-tools`](https://github.com/jazzband/pip-tools/) to manage dependencies.

### 1. Create a virtualenv

Note: Creating the virtualenv can be done however you want. We will assume you've done created a new
virtualenv and activated it from this point.

### 2. Install `pip-tools`:

```shell
pip install pip-tools
```

### 3. Install Dependencies

```shell
pip-sync requirements/core.txt requirements/dev.txt 
```
