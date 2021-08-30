from hypothesis import given, strategies as st
import pytest

from phx_events import json_handler


@given(st.text() | st.integers() | st.datetimes() | st.floats() | st.booleans())
def test_raises_type_error_if_not_a_decimal(obj):
    with pytest.raises(TypeError):
        json_handler.decimal_serialiser(obj)


@given(st.decimals(allow_nan=False))
def test_returns_serialised_decimals(decimal_obj):
    serialised_decimal = json_handler.decimal_serialiser(decimal_obj)

    expected_serialisation = float(str(decimal_obj))

    assert isinstance(serialised_decimal, float)
    assert serialised_decimal == expected_serialisation
