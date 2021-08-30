from decimal import Decimal
from typing import Any, Union

import orjson


def decimal_serialiser(_obj: Any) -> float:
    if isinstance(_obj, Decimal):
        return float(str(_obj))

    raise TypeError


def deep_float_replace(obj: Any) -> Any:
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {key: deep_float_replace(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [deep_float_replace(value) for value in obj]
    else:
        return obj


def dumps(obj: Any) -> bytes:
    return orjson.dumps(obj, default=decimal_serialiser)


def loads(json: Union[bytes, bytearray, memoryview, str], floats_to_decimal: bool = True) -> Any:
    parsed_json = orjson.loads(json)

    if not floats_to_decimal:
        return parsed_json

    return deep_float_replace(parsed_json)
