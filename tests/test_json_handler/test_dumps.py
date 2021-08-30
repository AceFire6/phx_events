from datetime import datetime
from decimal import Decimal

from phx_events import json_handler


def test_dumps_returns_json_string_and_handles_decimals():
    test_datetime = datetime(2021, 8, 30, 15, 56, 39, 1254)
    dump_dict = {
        'float': 1.5555,
        'decimals': [Decimal('1.3'), Decimal('2.6689')],
        'datetime': test_datetime,
        'deeper_dict': {
            'list': ['a', 'b', 'c', test_datetime],
            'text': 'Yes!',
        },
    }

    dict_json = json_handler.dumps(dump_dict)

    assert dict_json == (
        '{"float":1.5555,'
        '"decimals":[1.3,2.6689],'
        '"datetime":"2021-08-30T15:56:39.001254",'
        '"deeper_dict":{"list":["a","b","c","2021-08-30T15:56:39.001254"],"text":"Yes!"}}'
    ).encode()
