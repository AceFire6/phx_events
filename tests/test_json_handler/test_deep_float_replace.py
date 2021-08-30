from decimal import Decimal

from hypothesis import given, strategies as st

from phx_events import json_handler


@given(st.floats(allow_nan=False))
def test_returns_decimal_if_obj_is_float(float_obj):
    decimal_replaced_float = json_handler.deep_float_replace(float_obj)

    assert isinstance(decimal_replaced_float, Decimal)
    assert decimal_replaced_float == Decimal(str(float_obj))


@given(st.integers() | st.decimals(allow_nan=False) | st.text() | st.datetimes())
def test_returns_obj_if_not_float(obj):
    assert json_handler.deep_float_replace(obj) == obj


@given(st.lists(st.floats(allow_nan=False)))
def test_converts_elements_of_a_list(float_list_obj):
    decimal_replaced_list = json_handler.deep_float_replace(float_list_obj)

    expected_result = [Decimal(str(value)) for value in float_list_obj]

    assert all(isinstance(value, Decimal) for value in decimal_replaced_list)
    assert decimal_replaced_list == expected_result


@given(st.dictionaries(st.text(), st.floats(allow_nan=False)))
def test_converts_elements_of_a_dict(float_dict_obj):
    decimal_replaced_dict = json_handler.deep_float_replace(float_dict_obj)

    expected_result = {key: Decimal(str(value)) for key, value in float_dict_obj.items()}

    assert all(isinstance(value, Decimal) for value in decimal_replaced_dict.values())
    assert decimal_replaced_dict == expected_result


def test_converts_floats_in_complex_object():
    complex_object = [
        {
            'some_floats': [1.2, 1.3, 1.4, '1.5'],
            'all_floats': {
                'float_1': 1.0,
                'float_2': 2.0,
                'float_3-5': [3.0, 4.0, 5.0],
            },
        },
        [1.555, 2.555, 3.555],
    ]

    converted_complex_object = json_handler.deep_float_replace(complex_object)

    assert converted_complex_object == [
        {
            'some_floats': [Decimal('1.2'), Decimal('1.3'), Decimal('1.4'), '1.5'],
            'all_floats': {
                'float_1': Decimal('1.0'),
                'float_2': Decimal('2.0'),
                'float_3-5': [Decimal('3.0'), Decimal('4.0'), Decimal('5.0')],
            },
        },
        [Decimal('1.555'), Decimal('2.555'), Decimal('3.555')],
    ]
