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
    assert hasattr(meta, "func")  # Check if it's FunctionMetadata
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


def test_stateful_class_multiple_instances():
    from bridges.core.basic import Bridge
    from bridges.core.types import InputParamSource, DisplayOutputDestination

    class Counter:
        def __init__(self, start: int = 0):
            self.value = start
        def increment(self, amount: int = 1):
            self.value += amount
            return self.value
        def reset(self):
            self.value = 0
            return self.value

    bridge = Bridge("ObjTest")
    display = [DisplayOutputDestination()]
    bridge.register_class(
        Counter,
        params={
            "start": InputParamSource(default=0),
            "instance_name": InputParamSource(default=None)
        },
        output=display,
        methods=[
            {
                "name": "increment",
                "params": {
                    "amount": InputParamSource(default=1),
                    "instance_name": InputParamSource(default=None)
                },
                "output": display
            },
            {
                "name": "reset",
                "params": {
                    "instance_name": InputParamSource(default=None)
                },
                "output": display
            }
        ]
    )
    # Create two named instances
    bridge.functions["create_counter_instance"]({"start": 10, "instance_name": "foo"})
    bridge.functions["create_counter_instance"]({"start": 100, "instance_name": "bar"})
    # Increment each
    res_foo = bridge.functions["Counter.increment"]({"amount": 5, "instance_name": "foo"})
    res_bar = bridge.functions["Counter.increment"]({"amount": 7, "instance_name": "bar"})
    assert res_foo == 15
    assert res_bar == 107
    # Reset foo
    bridge.functions["Counter.reset"]({"instance_name": "foo"})
    # Check values
    foo = bridge.context["Counter_instance:foo"]
    bar = bridge.context["Counter_instance:bar"]
    assert foo.value == 0
    assert bar.value == 107
    # List all instances
    instances = bridge.list_all_instances()
    assert "Counter" in instances
    assert set(instances["Counter"]) == {"foo", "bar"}
