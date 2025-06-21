from bridges.core.basic import Bridge
from bridges.core.types import (
    InputParamSource,
    MenuParamSource,
    DisplayOutputDestination,
)
from bridges.core.cli import MinimalCLI


def calculate(a: int, b: int, op: str) -> int:
    """Perform a calculation on two numbers with the given operator."""
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        return a / b
    else:
        raise ValueError("Invalid operator")


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def greet(name: str, excited: bool = False) -> str:
    """Greet a user, optionally with excitement."""
    if excited:
        return f"Hello, {name}! 😃"
    return f"Hello, {name}."


if __name__ == "__main__":
    # Create the bridge
    bridge: Bridge = Bridge("POCBridge")

    # Register 'add' with explicit params and output
    bridge.register(
        add,
        params={"a": InputParamSource(), "b": InputParamSource()},
        output=DisplayOutputDestination(format="Sum: {value}"),
    )

    # Register 'calculate' with explicit params and custom output format
    bridge.register(
        calculate,
        params={
            "a": InputParamSource(),
            "b": InputParamSource(),
            "op": MenuParamSource(["+", "-", "*", "/"], default="+"),
        },
        output=DisplayOutputDestination(format="Result: {value}"),
    )

    # Register 'greet' WITHOUT specifying params to show automatic extraction
    bridge.register(
        greet,
        output=DisplayOutputDestination(format="Greeting: {value}"),
    )

    # Start the CLI
    cli: MinimalCLI = MinimalCLI(bridge)
    cli.run()
