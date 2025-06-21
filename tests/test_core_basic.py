"""
tests.test_core_basic
Basic tests for bridges core minimal implementation.
"""
import pytest
from bridges.core.basic import Bridge, FunctionMetadata
from bridges.core.types import InputParamSource, DisplayOutputDestination

def test_bridge_register_and_call():
    def add(a, b):
        return int(a) + int(b)

    bridge = Bridge("TestBridge")
    meta = bridge.register(
        add,
        params={"a": InputParamSource(), "b": InputParamSource()},
        output=DisplayOutputDestination()
    )
    assert isinstance(meta, FunctionMetadata)
    assert "add" in bridge.functions
    # Simulate call
    result = bridge.functions["add"].func(2, 3)
    assert result == 5
