# bridges

**A modern, framework-agnostic Python middleware for modular function registration, typed parameter and output handling, and automatic interface generation.**

**Version: 0.2.0**

---

## 🚀 What is bridges?

`bridges` lets you turn any Python function into a modular, type-safe, and interface-ready "bridge"—with automatic parameter extraction, validation, and rich metadata. Build custom UIs, CLIs, or APIs on top of your business logic, with zero boilerplate.

---

## ✨ Features

- **Register any Python function** as a modular, typed bridge
- **Automatic parameter extraction** and Pydantic validation
- **Rich parameter metadata**: descriptions, defaults, validators, required/optional flags
- **Extensible parameter sources**: Input, Menu, List, File, Context, and more
- **Multiple output destinations**: display, file, context, or custom
- **Event hooks** for pre/post/error handling
- **Context management** with history and snapshots
- **Framework-agnostic**: build your own UI, API, or CLI
- **Multi-bridge support**: run and switch between multiple bridges in one CLI
- **Object handling**: stateful class registration, multiple named instances, context isolation

---

## 🛠️ Installation

```bash
pip install bridges
# or for development:
git clone https://github.com/your-org/bridges.git
cd bridges
pip install -e .
```

---

## ⚡ Quick Start

```python
from bridges.core.basic import Bridge
from bridges.core.types import InputParamSource, DisplayOutputDestination
from bridges.interfaces.cli import CLI

def add(a: int, b: int) -> int:
    return a + b

bridge = Bridge("Demo")
bridge.register(
    add,
    params={"a": InputParamSource(), "b": InputParamSource()},
    output=DisplayOutputDestination()
)

CLI(bridge, name="MyApp Console", description="A custom workflow interface").run()
```

---

## 🖥️ Interfaces

- **UI-agnostic**: Build your own web, API, or GUI interface using the core abstractions.
- **CLI included**: Use the built-in CLI for instant interactive workflows (not required).

### CLI Highlights

- Customizable prompt and banner
- Rich output: colored panels, tables, and prompts
- Command history, aliases, and detailed help
- Graceful, styled error messages
- Parameter descriptions and validation feedback

---

## 🧑‍💻 Advanced Example

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

def log_pre(params, meta):
    print(f"[LOG] Calling {meta.name} with params: {params}")

bridge.add_pre_hook(log_pre)

CLI(bridge, name="Math Workflow Console", description="A workflow for math operations").run()
```

---

## 🏗️ Core Concepts

### Parameter Sources

- **InputParamSource**: Direct user input (with defaults, validation)
- **MenuParamSource**: Select from options (supports Enums)
- **ListParamSource**: Multi-value input with custom separators
- **FileParamSource**: File content as parameter value
- **ContextParamSource**: Values from bridge context
- **Custom**: Extend `ParamSource` for your own logic

### Output Destinations

- **DisplayOutputDestination**: Rich formatted output
- **FileOutputDestination**: Write results to files
- **ContextOutputDestination**: Store in bridge context
- **Custom**: Extend `OutputDestination` for your own needs

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

---

## 🧩 Extending bridges

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

---

## 🧪 Testing

```bash
pytest
```

---

## 📄 License

MIT

---

## 📜 Changelog

See `CHANGELOG.md` for highlights.

## Multi-Bridge CLI Usage
- Use `switch <bridge>` to change the active bridge.
- Use `bridges` to list all available bridges.
- Each bridge has its own context, functions, and state.

## CLI Commands
- `help` - Show help
- `list` - List functions
- `info <function>` - Show function info
- `instances` - List all class instances
- `bridges` - List all bridges (multi-bridge mode)
- `switch <bridge>` - Switch active bridge
- `quit` - Exit

