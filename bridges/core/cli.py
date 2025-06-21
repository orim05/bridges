"""
bridges.core.cli
Minimal CLI interface for bridges core.
"""

from typing import Any, Dict
from .base import BridgeInterface, IBridge
import inspect


class MinimalCLI(BridgeInterface):
    """
    Minimal CLI interface for a bridge.
    """

    def customize(self, config: Dict[str, Any]):
        # No-op for minimal version
        pass

    def run(self):
        print(f"\n{self.bridge.name} CLI v{self.bridge.version}")
        print("Type 'help' for available commands or 'exit' to quit.\n")
        while True:
            try:
                command = input(f"{self.bridge.name} > ").strip()
                if not command:
                    continue
                if command.lower() in ("exit", "quit", "q"):
                    print("Goodbye!")
                    break
                if command.lower() == "help":
                    print("\nAvailable commands:")
                    for name, meta in self.bridge.functions.items():
                        print(f"  {name}: {meta.description}")
                    print()
                    continue
                if command in self.bridge.functions:
                    meta = self.bridge.functions[command]
                    params = {}
                    sig = inspect.signature(meta.func)
                    for pname in meta.params:
                        ptype = sig.parameters[pname].annotation
                        val = input(f"{pname}: ")
                        # Convert to correct type if possible
                        if ptype is int:
                            val = int(val)
                        elif ptype is float:
                            val = float(val)
                        elif ptype is bool:
                            val = val.lower() in ("1", "true", "yes", "y")
                        # else leave as str
                        params[pname] = val
                    result = meta.func(**params)
                    print(f"\nResult: {result}\n")
                else:
                    print(f"Unknown command: {command}")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
