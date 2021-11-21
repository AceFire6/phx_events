from typing import TypeVar, AsyncIterator

T = TypeVar('T')


async def async_iter(*items: T) -> AsyncIterator[T]:
    for item in items:
        yield item
