"""
bridges.interfaces.cli.core

Core CLI interface for bridges framework.
"""

from typing import Any, Dict

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from ...core.base import BridgeInterface
from .display import HelpDisplay, ResultDisplay
from .prompts import ParameterCollector


class CLI(BridgeInterface):
    """
    Rich command-line interface for bridges with modern styling.
    """

    def __init__(self, bridge, name: str = "CLI", description: str = ""):
        super().__init__(bridge)
        self.console = Console()
        self.name = name
        self.description = description
        self.config = {
            "prompt": f"{self.name}> ",
            "theme": "blue",
            "show_banner": True,
            "banner_name": self.name,
            "banner_description": self.description,
        }
        self.history = []
        self.command_aliases = {}
        self.param_collector = ParameterCollector(self.console)
        self.result_display = ResultDisplay(self.console)
        self.help_display = HelpDisplay(self.console)

    def customize(self, config: Dict[str, Any]):
        """Customize the CLI with configuration options."""
        self.config.update(config)
        # Update name/description if provided
        if "banner_name" in config:
            self.name = config["banner_name"]
        if "banner_description" in config:
            self.description = config["banner_description"]
        if "prompt" in config:
            self.config["prompt"] = config["prompt"]
        else:
            self.config["prompt"] = f"{self.name}> "

    def _print_banner(self):
        """Print the CLI banner."""
        if self.config.get("show_banner", True):
            banner = Text(self.name, style="bold blue")
            subtitle = Text(self.description, style="dim") if self.description else ""
            panel = Panel(
                f"{banner}\n{subtitle}" if subtitle else f"{banner}",
                box=box.ROUNDED,
                style="blue",
                padding=(1, 2)
            )
            self.console.print(panel)
            self.console.print()

    def run(self):
        """Run the CLI interface."""
        self._print_banner()
        
        if not self.bridge.functions:
            self.console.print("[yellow]No functions registered.[/yellow]")
            return

        self.console.print("[dim]Type 'help' for available commands[/dim]\n")

        while True:
            try:
                # Get command with rich prompt
                command = Prompt.ask(self.config["prompt"]).strip()
                
                if not command:
                    continue

                # Add to history
                self.history.append(command)
                
                # Parse command
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                # Handle built-in commands
                if cmd in ['help', 'h']:
                    self.help_display.print_help()
                elif cmd in ['list', 'ls', 'l']:
                    self.help_display.list_functions(self.bridge)
                elif cmd in ['info', 'i']:
                    if args:
                        self.help_display.show_function_info(self.bridge, args[0])
                    else:
                        self.console.print("[red]Usage: info <function_name>[/red]")
                elif cmd in ['quit', 'exit', 'q']:
                    if Confirm.ask("Are you sure you want to exit?"):
                        self.console.print("[green]Goodbye! 👋[/green]")
                        break
                elif cmd in self.bridge.functions:
                    # Execute function
                    func_meta = self.bridge.functions[cmd]
                    params = self.param_collector.collect_parameters(func_meta)
                    
                    if params is None:  # User cancelled
                        continue

                    # Execute and show result
                    try:
                        result = func_meta(params)
                        self.result_display.display_result(result)
                    except Exception as e:
                        self.console.print(f"[red]Error executing function: {e}[/red]")
                else:
                    self.console.print(f"[red]Unknown command: {cmd}[/red]")
                    self.console.print("[dim]Type 'help' for available commands[/dim]")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except EOFError:
                self.console.print("\n[green]Goodbye! 👋[/green]")
                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {e}[/red]")


# Alias for backward compatibility
SimpleCLI = CLI 