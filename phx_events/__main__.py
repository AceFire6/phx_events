from anyio import run

from phx_events.async_logger import async_logger


logger = async_logger.getChild(__name__)


async def main():
    logger.info('Hello, world!')


if __name__ == '__main__':
    run(main)
