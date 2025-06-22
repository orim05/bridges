"""
tests.test_core_basic
Basic tests for bridges core minimal implementation.
"""

from bridges.core.basic import Bridge
from bridges.core.types import DisplayOutputDestination, InputParamSource


def test_bridge_register_and_call():
    def add(a, b):
        return int(a) + int(b)

    bridge = Bridge("TestBridge")
    meta = bridge.register(
        add,
        params={"a": InputParamSource(), "b": InputParamSource()},
        output=DisplayOutputDestination(),
    )
    assert hasattr(meta, 'func')  # Check if it's FunctionMetadata
    assert "add" in bridge.functions
    # Simulate call
    result = bridge.functions["add"].func(2, 3)
    assert result == 5


def test_auto_param_extraction():
    def greet(name: str, excited: bool = False) -> str:
        if excited:
            return f"Hello, {name}! 😃"
        return f"Hello, {name}."

    bridge = Bridge("TestBridgeAuto")
    bridge.register(
        greet,
        output=DisplayOutputDestination(),
    )
    assert "greet" in bridge.functions
    # Simulate call with and without default
    assert bridge.functions["greet"].func("Alice") == "Hello, Alice."
    assert bridge.functions["greet"].func("Bob", True) == "Hello, Bob! 😃"
