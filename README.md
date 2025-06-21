# bridges
A framework-agnostic middleware for automatic UI generation

## Features
- Register any Python function and get an instant CLI
- Extensible parameter and output types
- Minimal, composable core for building custom UIs

## Quick Start
```python
from bridges.core.basic import Bridge
from bridges.core.types import InputParamSource, DisplayOutputDestination
from bridges.core.cli import MinimalCLI

def add(a, b):
    return int(a) + int(b)

bridge = Bridge("Demo")
bridge.register(
    add,
    params={"a": InputParamSource(), "b": InputParamSource()},
    output=DisplayOutputDestination()
)
cli = MinimalCLI(bridge)
cli.run()
```

## Advanced Example: Custom Parameter Types and Output
```python
from bridges.core.basic import Bridge
from bridges.core.types import InputParamSource, MenuParamSource, DisplayOutputDestination
from bridges.core.cli import MinimalCLI

def calculate(a: int, b: int, op: str) -> int:
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        return a / b

bridge: Bridge = Bridge("AdvancedDemo")
bridge.register(
    calculate,
    params={
        "a": InputParamSource(),
        "b": InputParamSource(),
        "op": MenuParamSource(["+", "-", "*", "/"], default="+")
    },
    output=DisplayOutputDestination(format="Result: {value}")
)
cli: MinimalCLI = MinimalCLI(bridge)
cli.run()
```

## Testing
Run all tests with:
```
pytest
```

## License
MIT

