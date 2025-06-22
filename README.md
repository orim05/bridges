# bridges

A modern, framework-agnostic Python middleware for modular function registration, typed parameter and output handling, and automatic interface generation.

**Version: 0.2.0**

## Features
- Register any Python function as a modular, typed "bridge"
- Automatic parameter extraction and Pydantic validation
- Rich parameter metadata: descriptions, defaults, validators, required/optional flags
- Extensible parameter sources: Input, Menu, List, File, Context, and more
- Multiple output destinations: display, file, context, custom
- Event hooks for pre/post/error handling
- Context management with history and snapshots
- Framework-agnostic, composable core for building custom UIs and workflows
- Optional built-in CLI interface (with [rich](https://github.com/Textualize/rich)) as an example (not a "Bridge CLI")
- Type safe and fully typed

## Installation
```bash
pip install bridges  # or clone and pip install -e .
```

## Quick Start
```python
from bridges.core.basic import Bridge
from bridges.core.types import InputParamSource, DisplayOutputDestination
from bridges.interfaces.cli import CLI  # Example interface

def add(a: int, b: int) -> int:
    return a + b

bridge = Bridge("Demo")
bridge.register(
    add,
    params={"a": InputParamSource(), "b": InputParamSource()},
    output=DisplayOutputDestination()
)
# The CLI is a generic interface; you can set its name and description:
CLI(bridge, name="MyApp Console", description="A custom workflow interface").run()
```

## Interfaces
bridges is UI-agnostic. You can:
- Build your own web, API, or GUI interface using the core abstractions
- Use the included CLI as a ready-to-go example (not required)

### Example: CLI Experience
- Prompt: `MyApp Console> ` (customizable)
- Rich output: colored panels, tables, and prompts
- Banner, command history, aliases, and detailed help
- Graceful, styled error messages
- Parameter descriptions and validation feedback

## Advanced Example
```python
from enum import Enum
from bridges.core.basic import Bridge
from bridges.core.types import (
    InputParamSource, MenuParamSource, ListParamSource, 
    DisplayOutputDestination, ContextOutputDestination,
    ParameterMetadata
)
from bridges.interfaces.cli import CLI

class Operation(Enum):
    ADD = "Add"
    MULTIPLY = "Multiply"

def operate(a: int, b: int, op: Operation) -> int:
    if op == Operation.ADD:
        return a + b
    elif op == Operation.MULTIPLY:
        return a * b
    raise ValueError("Unknown operation")

def sum_list(numbers: list[int]) -> int:
    return sum(numbers)

bridge = Bridge("MathWorkflow")

# Register with parameter metadata
bridge.register(
    operate,
    params={
        "a": ParameterMetadata(
            description="First number",
            required=True,
            default=lambda: bridge.context.get("last_result", 1)
        ),
        "b": ParameterMetadata(
            description="Second number", 
            required=True, 
            default=1
        ),
        "op": MenuParamSource(Operation),
    },
    output=[
        DisplayOutputDestination(format="Result: {value}"),
        ContextOutputDestination(key="last_result"),
    ]
)

# Register list parameter
bridge.register(
    sum_list,
    params={
        "numbers": ListParamSource(description="Numbers to sum", default=[1, 2, 3]),
    },
    output=[
        DisplayOutputDestination(format="Sum of list: {value}"),
        ContextOutputDestination(key="last_result"),
    ]
)

# Add event hooks
def log_pre(params, meta):
    print(f"[LOG] Calling {meta.name} with params: {params}")

bridge.add_pre_hook(log_pre)
# Set a custom interface name/description for the CLI
CLI(bridge, name="Math Workflow Console", description="A workflow for math operations").run()
```

## Core Features

### Parameter Sources
- **InputParamSource**: Direct user input with defaults and validation
- **MenuParamSource**: Selection from options (supports Enums)
- **ListParamSource**: Collection of values with custom separators
- **FileParamSource**: File content as parameter value
- **ContextParamSource**: Values from bridge context
- **Custom sources**: Extend ParamSource base class

### Output Destinations
- **DisplayOutputDestination**: Rich formatted output
- **FileOutputDestination**: Write results to files
- **ContextOutputDestination**: Store in bridge context
- **Custom destinations**: Extend OutputDestination base class

### Parameter Metadata
```python
ParameterMetadata(
    description="Parameter description",
    required=True,
    default=42,
    validator=lambda x: x > 0
)
```

### Context Management
```python
bridge.update_context("key", value)
bridge.clear_context()
bridge.restore_context(index)
bridge.get_context_history()
```

### Event Hooks
```python
bridge.add_pre_hook(lambda params, meta: print(f"Pre: {meta.name}"))
bridge.add_post_hook(lambda result, meta: print(f"Post: {result}"))
bridge.add_error_hook(lambda exc, meta: print(f"Error: {exc}"))
```

## Extending
Register custom parameter sources and outputs:
```python
from bridges.core.types import ParamSource, OutputDestination

class MyParamSource(ParamSource):
    def get_value(self, context):
        return "custom_value"

class MyOutputDestination(OutputDestination):
    def send(self, value, context):
        pass
```

## Testing
```bash
pytest
```

## License
MIT

## Changelog
See `CHANGELOG.md` for highlights.

