"""
bridges.interfaces.cli.display

Display logic for CLI interface results and help.
"""

from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class ResultDisplay:
    """Handles result display formatting."""

    def __init__(self, console: Console):
        self.console = console

    def display_result(self, result: Any):
        """Display the result with rich formatting."""
        if result is None:
            self.console.print("[dim]Function completed (no output)[/dim]")
            return

        # Try to format the result nicely
        if isinstance(result, dict):
            table = Table(title="[bold green]Result[/bold green]", show_header=True, header_style="bold green")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="white")
            
            for key, value in result.items():
                table.add_row(str(key), str(value))
            
            self.console.print(table)
        elif isinstance(result, (list, tuple)):
            if len(result) > 10:
                self.console.print(f"[bold green]Result:[/bold green] {len(result)} items")
                for i, item in enumerate(result[:5]):
                    self.console.print(f"  {i}: {item}")
                self.console.print(f"  ... and {len(result) - 5} more items")
            else:
                self.console.print("[bold green]Result:[/bold green]")
                for i, item in enumerate(result):
                    self.console.print(f"  {i}: {item}")
        else:
            self.console.print(f"[bold green]Result:[/bold green] {result}")


class HelpDisplay:
    """Handles help and function information display."""

    def __init__(self, console: Console):
        self.console = console

    def print_help(self):
        """Print help information."""
        help_text = """
[bold]Available Commands:[/bold]
  [cyan]help[/cyan]                    - Show this help message
  [cyan]list[/cyan]                   - List all available functions
  [cyan]info <function>[/cyan]        - Show detailed function information
  [cyan]quit[/cyan], [cyan]exit[/cyan], [cyan]q[/cyan]  - Exit the CLI

[bold]Function Execution:[/bold]
  Simply type the function name to execute it interactively.

[bold]Examples:[/bold]
  [green]<function_name>[/green]      - Execute a function
  [green]info <function_name>[/green] - Show details about a function
        """
        
        panel = Panel(help_text, title="[bold blue]Help[/bold blue]", box=box.ROUNDED)
        self.console.print(panel)

    def list_functions(self, bridge):
        """List all available functions in a table."""
        if not bridge.functions:
            self.console.print("[yellow]No functions registered.[/yellow]")
            return

        table = Table(title=f"[bold blue]Available Functions in {bridge.name}[/bold blue]")
        table.add_column("Function", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Parameters", style="dim")

        for name, func_meta in bridge.functions.items():
            param_count = len(func_meta.params) if func_meta.params else 0
            description = func_meta.description or "No description"
            table.add_row(name, description, f"{param_count} params")

        self.console.print(table)

    def show_function_info(self, bridge, func_name: str):
        """Show detailed information about a function."""
        if func_name not in bridge.functions:
            self.console.print(f"[red]Function '{func_name}' not found.[/red]")
            return

        func_meta = bridge.functions[func_name]
        
        # Function header
        header = f"[bold blue]{func_name}[/bold blue]"
        if func_meta.description:
            header += f"\n[dim]{func_meta.description}[/dim]"
        
        # Parameters table
        param_table = Table(title="Parameters", show_header=True, header_style="bold magenta")
        param_table.add_column("Parameter", style="cyan")
        param_table.add_column("Type", style="green")
        param_table.add_column("Required", style="yellow")
        param_table.add_column("Default", style="dim")
        param_table.add_column("Description", style="white")

        for param_name, param_meta in func_meta.params.items():
            # Handle type display safely
            if hasattr(param_meta, 'element_type'):
                element_type = param_meta.element_type
                if element_type is None:
                    param_type = "any"
                elif hasattr(element_type, '__name__'):
                    param_type = element_type.__name__
                else:
                    param_type = str(element_type)
            else:
                # For ParameterMetadata and other param sources without element_type
                param_type = type(param_meta).__name__.replace('ParamSource', '').replace('ParameterMetadata', 'any')
            
            required = "Yes" if not hasattr(param_meta, 'default') or param_meta.default is None else "No"
            default = str(param_meta.default) if hasattr(param_meta, 'default') and param_meta.default is not None else "-"
            description = getattr(param_meta, 'description', '') or '-'
            
            param_table.add_row(param_name, param_type, required, default, description)

        # Output information
        output_info = ""
        if hasattr(func_meta, 'output') and func_meta.output:
            output_info = "\n[bold]Outputs:[/bold]\n"
            for i, output in enumerate(func_meta.output):
                output_info += f"  {i+1}. {type(output).__name__}\n"

        # Display everything
        self.console.print(Panel(header, title="[bold blue]Function Information[/bold blue]", box=box.ROUNDED))
        if param_table.row_count > 0:
            self.console.print(param_table)
        if output_info:
            self.console.print(output_info) 