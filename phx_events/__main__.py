from anyio import run

from phx_events.async_logger import logger


async def main():
    logger.info('Hello, world!')


if __name__ == '__main__':
    run(main)
