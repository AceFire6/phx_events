from decimal import Decimal
from typing import Any, Union

import orjson


def serialiser(_obj: Any) -> str:
    if isinstance(_obj, Decimal):
        return str(_obj)

    raise TypeError


def dumps(obj: Any) -> bytes:
    return orjson.dumps(obj, default=serialiser)


def loads(json: Union[bytes, bytearray, memoryview, str]) -> Any:
    return orjson.loads(json)
