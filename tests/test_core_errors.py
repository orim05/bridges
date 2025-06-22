"""
tests.test_core_errors
Test error handling in bridges core.
"""
import pytest

from bridges.core.basic import Bridge
from bridges.core.types import DisplayOutputDestination, InputParamSource


def test_validation_error():
    def add_positive(a: int):
        if a < 0:
            raise ValueError("Negative not allowed")
        return a
    bridge = Bridge("TestErrors")
    meta = bridge.register(
        add_positive,
        params={"a": InputParamSource()},
        output=DisplayOutputDestination(),
    )
    # Simulate validation error (missing param)
    with pytest.raises(TypeError):
        meta.func()
    # Simulate execution error
    with pytest.raises(ValueError):
        meta.func(-1) 