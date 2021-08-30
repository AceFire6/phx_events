from datetime import datetime
from decimal import Decimal

from phx_events import json_handler


def test_loads_returns_dictionary_and_handles_decimals_when_floats_to_decimal_true():
    json_bytes = (
        '{"float":1.5555,'
        '"decimals":[1.3,2.6689],'
        '"datetime":"2021-08-30T15:56:39.001254",'
        '"deeper_dict":{"list":["a","b","c","2021-08-30T15:56:39.001254"],"text":"Yes!"}}'
    ).encode()

    expected_datetime = datetime(2021, 8, 30, 15, 56, 39, 1254)
    expected_dict = {
        'float': Decimal('1.5555'),
        'decimals': [Decimal('1.3'), Decimal('2.6689')],
        'datetime': expected_datetime.isoformat(),
        'deeper_dict': {
            'list': ['a', 'b', 'c', expected_datetime.isoformat()],
            'text': 'Yes!',
        },
    }

    json_dict = json_handler.loads(json_bytes)

    assert json_dict == expected_dict


def test_loads_returns_dictionary_and_leaves_floats_as_floats_when_floats_to_decimal_false():
    json_bytes = (
        '{"float":1.5555,'
        '"decimals":[1.3,2.6689],'
        '"datetime":"2021-08-30T15:56:39.001254",'
        '"deeper_dict":{"list":["a","b","c","2021-08-30T15:56:39.001254"],"text":"Yes!"}}'
    ).encode()

    expected_datetime = datetime(2021, 8, 30, 15, 56, 39, 1254)
    expected_dict = {
        'float': 1.5555,
        'decimals': [1.3, 2.6689],
        'datetime': expected_datetime.isoformat(),
        'deeper_dict': {
            'list': ['a', 'b', 'c', expected_datetime.isoformat()],
            'text': 'Yes!',
        },
    }

    json_dict = json_handler.loads(json_bytes, floats_to_decimal=False)

    assert json_dict == expected_dict
