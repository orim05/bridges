"""
bridges.interfaces.cli.prompts

Parameter collection logic for CLI interface.
"""

from typing import Any, Dict, Optional

from rich.console import Console
from rich.prompt import Prompt


class ParameterCollector:
    """Handles parameter collection for different parameter source types."""

    def __init__(self, console: Console):
        self.console = console

    def collect_parameters(self, func_meta) -> Optional[Dict[str, Any]]:
        """Collect parameters for a function with rich prompts."""
        params = {}

        self.console.print(f"\n[bold green]Executing: {func_meta.name}[/bold green]")
        self.console.print("[dim]Press Ctrl+C to cancel[/dim]\n")

        # Get bridge context if available
        bridge = getattr(func_meta, "bridge", None)
        context = getattr(bridge, "context", {}) if bridge else {}

        for param_name, param_meta in func_meta.params.items():
            # Auto-fill from context for ContextParamSource
            if type(param_meta).__name__ == "ContextParamSource":
                value = param_meta.get_value(context)
                params[param_name] = value
                self.console.print(
                    f"[cyan]{param_name}[/cyan] (from context: '{param_meta.key}') [green]Auto-filled: {value}[/green]"
                )
                continue
            try:
                # Parameter header
                param_header = f"[bold cyan]{param_name}[/bold cyan]"
                if hasattr(param_meta, "description") and param_meta.description:
                    param_header += f" - [dim]{param_meta.description}[/dim]"
                self.console.print(param_header)

                if hasattr(param_meta, "options"):  # MenuParamSource
                    self._collect_menu_param(param_name, param_meta, params)
                elif hasattr(param_meta, "separator"):  # ListParamSource
                    self._collect_list_param(param_name, param_meta, params)
                elif hasattr(param_meta, "mode"):  # FileParamSource
                    self._collect_file_param(param_name, param_meta, params)
                else:  # Default input
                    self._collect_input_param(param_name, param_meta, params)

                self.console.print()  # Add spacing between parameters

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Cancelled.[/yellow]")
                return None

        return params

    def _collect_menu_param(self, param_name: str, param_meta, params: Dict[str, Any]):
        """Collect menu parameter selection."""
        self.console.print("[yellow]Available options:[/yellow]")
        for i, (label, value) in enumerate(param_meta.options):
            marker = (
                "→"
                if hasattr(param_meta, "default") and param_meta.default == value
                else " "
            )
            self.console.print(f"  {marker} [cyan]{i}[/cyan]: {label}")

        while True:
            choice = Prompt.ask(
                "Select option",
                choices=[str(i) for i in range(len(param_meta.options))],
                default=(
                    str(
                        param_meta.options.index(
                            (param_meta.default, param_meta.default)
                        )
                    )
                    if hasattr(param_meta, "default") and param_meta.default
                    else None
                ),
            )
            try:
                index = int(choice)
                if 0 <= index < len(param_meta.options):
                    params[param_name] = param_meta.options[index][1]
                    self.console.print(
                        f"[green]Selected: {param_meta.options[index][0]}[/green]"
                    )
                    break
                else:
                    self.console.print("[red]Invalid option.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")

    def _collect_list_param(self, param_name: str, param_meta, params: Dict[str, Any]):
        """Collect list parameter input."""
        prompt_text = f"Enter values (separated by '{param_meta.separator}')"
        if hasattr(param_meta, "default") and param_meta.default:
            prompt_text += f" [default: {param_meta.default}]"

        value = Prompt.ask(prompt_text)
        if value:
            # Convert string list to proper type
            items = [item.strip() for item in value.split(param_meta.separator)]
            if param_meta.element_type is not str:
                try:
                    items = [param_meta.element_type(item) for item in items]
                except (ValueError, TypeError):
                    self.console.print(f"[red]Invalid values for {param_name}[/red]")
                    return
            params[param_name] = items
            self.console.print(f"[green]Added {len(items)} items[/green]")
        elif hasattr(param_meta, "default") and param_meta.default:
            params[param_name] = param_meta.default
            self.console.print(f"[green]Using default: {param_meta.default}[/green]")

    def _collect_file_param(self, param_name: str, param_meta, params: Dict[str, Any]):
        """Collect file parameter input, handling both read and write modes."""
        mode = getattr(param_meta, "mode", "r")
        while True:
            file_path = Prompt.ask("Enter file path (or type 'cancel' to skip)")
            if not file_path or file_path.lower() == "cancel":
                self.console.print(
                    f"[yellow]Cancelled input for {param_name}.[/yellow]"
                )
                return
            if "r" in mode:
                try:
                    with open(file_path, mode) as f:
                        params[param_name] = f.read()
                    self.console.print(f"[green]File loaded: {file_path}[/green]")
                    break
                except FileNotFoundError:
                    self.console.print(f"[red]File not found: {file_path}[/red]")
                except Exception as e:
                    self.console.print(f"[red]Error reading file: {e}[/red]")
            elif any(m in mode for m in ["w", "a", "+"]):
                params[param_name] = file_path
                self.console.print(
                    f"[green]File path set for writing: {file_path}[/green]"
                )
                break
            else:
                self.console.print(
                    f"[red]Unsupported file mode: {mode} for {param_name}[/red]"
                )
                break

    def _collect_input_param(self, param_name: str, param_meta, params: Dict[str, Any]):
        """Collect basic input parameter."""
        prompt_text = "Enter value"
        if hasattr(param_meta, "default") and param_meta.default is not None:
            prompt_text += f" [default: {param_meta.default}]"

        value = Prompt.ask(prompt_text)
        if value:
            params[param_name] = value
            self.console.print(f"[green]Value set: {value}[/green]")
        elif hasattr(param_meta, "default") and param_meta.default is not None:
            params[param_name] = param_meta.default
            self.console.print(f"[green]Using default: {param_meta.default}[/green]")
