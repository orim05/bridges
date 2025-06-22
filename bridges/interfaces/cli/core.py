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
    Now supports interactive bridge switching if initialized with a bridge registry.
    """

    def __init__(self, bridge_or_registry, name: str = "CLI", description: str = ""):
        # Support both single bridge and registry of bridges
        if isinstance(bridge_or_registry, dict):
            self.bridges = bridge_or_registry
            # Default to the first bridge in the dict
            self.active_bridge_name = next(iter(self.bridges))
            self.bridge = self.bridges[self.active_bridge_name]
            self.multi_bridge = True
        else:
            self.bridges = None
            self.active_bridge_name = None
            self.bridge = bridge_or_registry
            self.multi_bridge = False
        super().__init__(self.bridge)
        self.console = Console()
        self.name = name
        self.description = description
        self.config = {
            "prompt": f"{self._make_prompt()}",
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
        self._func_name_map = {fname.lower(): fname for fname in self.bridge.functions}

    def _make_prompt(self):
        if self.multi_bridge:
            return f"{self.active_bridge_name}> "
        return f"{self.name}> "

    def customize(self, config: Dict[str, Any]):
        """Customize the CLI with configuration options."""
        super().customize(config)
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
                padding=(1, 2),
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
        self._func_name_map = {fname.lower(): fname for fname in self.bridge.functions}
        while True:
            try:
                command = Prompt.ask(self.config["prompt"]).strip()
                if not command:
                    continue
                self.history.append(command)
                self._handle_command(command)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except EOFError:
                self.console.print("\n[green]Goodbye! 👋[/green]")
                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {e}[/red]")

    def _handle_command(self, command: str):
        """Parse and handle a single CLI command."""
        parts = command.split()
        if not parts:
            return
        cmd_raw = parts[0]
        cmd = cmd_raw.lower()
        args = parts[1:] if len(parts) > 1 else []
        # Bridge switching
        if self.multi_bridge and cmd == "switch":
            self._handle_switch_command(args)
            return
        # Built-in commands
        if self._handle_builtin_command(cmd, args):
            return
        # Case-insensitive function lookup
        func_name = self._func_name_map.get(cmd)
        if func_name:
            self._execute_function_command(func_name)
        else:
            self.console.print(f"[red]Unknown command: {cmd_raw}[/red]")
            self.console.print("[dim]Type 'help' for available commands[/dim]")

    def _handle_switch_command(self, args):
        """Handle the 'switch' command for changing active bridge."""
        if not args:
            self.console.print("[red]Usage: switch <bridge_name>[/red]")
            return
        bname = args[0]
        if bname in self.bridges:
            self.active_bridge_name = bname
            self.bridge = self.bridges[bname]
            self._func_name_map = {fname.lower(): fname for fname in self.bridge.functions}
            self.config["prompt"] = self._make_prompt()
            self.console.print(f"[green]Switched to bridge: {bname}[/green]")
        else:
            self.console.print(f"[red]Unknown bridge: {bname}[/red]")

    def _handle_builtin_command(self, cmd: str, args: list) -> bool:
        """Handle built-in CLI commands. Returns True if handled."""
        if cmd in ["help", "h"]:
            self.help_display.print_help()
            return True
        elif cmd in ["list", "ls", "l"]:
            self.help_display.list_functions(self.bridge)
            return True
        elif cmd in ["info", "i"]:
            if args:
                self.help_display.show_function_info(self.bridge, args[0])
            else:
                self.console.print("[red]Usage: info <function_name>[/red]")
            return True
        elif cmd in ["instances", "list-instances"]:
            instances = self.bridge.list_all_instances()
            if not instances:
                self.console.print("[yellow]No class instances found in context.[/yellow]")
            else:
                self.console.print("[bold blue]Instances by class:[/bold blue]")
                for cls, names in instances.items():
                    self.console.print(f"[cyan]{cls}[/cyan]: {', '.join(names)}")
            return True
        elif cmd == "bridges":
            if getattr(self, "multi_bridge", False) and self.bridges:
                self.console.print("[bold blue]Available bridges:[/bold blue]")
                for bname in self.bridges:
                    if bname == self.active_bridge_name:
                        self.console.print(f"[green]{bname} (active)[/green]")
                    else:
                        self.console.print(f"[cyan]{bname}[/cyan]")
            else:
                self.console.print("[yellow]Only one bridge is active.[/yellow]")
            return True
        elif cmd in ["quit", "exit", "q"]:
            if Confirm.ask("Are you sure you want to exit?"):
                self.console.print("[green]Goodbye! 👋[/green]")
                exit(0)
            return True
        return False

    def _execute_function_command(self, cmd: str):
        """Collect parameters and execute a registered function command."""
        func_meta = self.bridge.functions[cmd]
        params = self.param_collector.collect_parameters(func_meta)
        if params is None:  # User cancelled
            return
        try:
            result = func_meta(params)
            self.result_display.display_result(result)
        except Exception as e:
            self.console.print(f"[red]Error executing function: {e}[/red]")
