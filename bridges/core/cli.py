"""
bridges.core.cli
Minimal CLI interface for bridges core.
"""

from typing import Any, Dict
from .base import BridgeInterface
import inspect


class MinimalCLI(BridgeInterface):
    """
    Minimal CLI interface for a bridge.
    """

    def customize(self, config: Dict[str, Any]):
        """
        Customize the CLI interface with the given configuration.

        :param config: Dictionary of configuration options.
        """
        # No-op for minimal version
        pass

    def run(self):
        """
        Run the CLI interface loop, handling user input and command execution.
        """
        self._print_banner()
        while True:
            try:
                command = input(f"{self.bridge.name} > ").strip()
                if not command:
                    continue
                if self._is_exit_command(command):
                    self._print_goodbye()
                    break
                if self._is_help_command(command):
                    self._print_help()
                    continue
                self._handle_command(command)
            except KeyboardInterrupt:
                self._print_goodbye()
                break

    def _print_banner(self):
        """
        Print the CLI banner with version and instructions.
        """
        print(f"\n{self.bridge.name} CLI v{self.bridge.version}")
        print("Type 'help' for available commands or 'exit' to quit.\n")

    def _is_exit_command(self, command: str) -> bool:
        """
        Check if the command is an exit command.

        :param command: The user input command string.
        :return: True if the command is an exit command, False otherwise.
        """
        return command.lower() in ("exit", "quit", "q")

    def _is_help_command(self, command: str) -> bool:
        """
        Check if the command is a help command.

        :param command: The user input command string.
        :return: True if the command is a help command, False otherwise.
        """
        return command.lower() == "help"

    def _print_help(self):
        """
        Print the list of available commands and their descriptions.
        """
        print("\nAvailable commands:")
        for name, meta in self.bridge.functions.items():
            print(f"  {name}: {meta.description}")
        print()

    def _print_goodbye(self):
        """
        Print a goodbye message and exit the CLI.
        """
        print("Goodbye!")

    def _handle_command(self, command: str):
        """
        Handle the execution of a user command.

        :param command: The user input command string.
        """
        if command in self.bridge.functions:
            meta = self.bridge.functions[command]
            params = self._collect_parameters(meta)
            result = meta.func(**params)
            self._display_result(result, meta)
        else:
            print(f"Unknown command: {command}")

    def _collect_parameters(self, meta):
        """
        Collect parameters for a function from user input.

        :param meta: FunctionMetadata object for the function.
        :return: Dictionary of parameter values.
        """
        params = {}
        sig = inspect.signature(meta.func)
        for pname, psource in meta.params.items():
            ptype = sig.parameters[pname].annotation
            val = self._prompt_for_param(pname, psource, ptype)
            params[pname] = val
        return params

    def _prompt_for_param(self, pname, psource, ptype):
        """
        Prompt the user for a parameter value, with type conversion.

        :param pname: Parameter name.
        :param psource: Parameter source object.
        :param ptype: Expected parameter type.
        :return: The value entered by the user, converted to the correct type if possible.
        """
        # Only InputParamSource supported in minimal version
        prompt = f"{pname}"
        if hasattr(psource, 'placeholder') and psource.placeholder:
            prompt += f" ({psource.placeholder})"
        if hasattr(psource, 'default') and psource.default is not None:
            prompt += f" [{psource.default}]"
        prompt += ": "
        val = input(prompt)
        if not val and hasattr(psource, 'default'):
            val = psource.default
        # Convert to correct type if possible
        if ptype is int:
            try:
                return int(val)
            except Exception:
                return val
        elif ptype is float:
            try:
                return float(val)
            except Exception:
                return val
        elif ptype is bool:
            return str(val).lower() in ("1", "true", "yes", "y")
        return val

    def _display_result(self, result, meta):
        """
        Display the result of a function call to the user.

        :param result: The result value to display.
        :param meta: FunctionMetadata object for the function.
        """
        # Only DisplayOutputDestination supported in minimal version
        output = getattr(meta, 'output', None)
        if hasattr(output, 'format'):
            print(f"\n{output.format.format(value=result)}\n")
        else:
            print(f"\nResult: {result}\n")
