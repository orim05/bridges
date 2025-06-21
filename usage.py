from enum import IntEnum
from typing import Union, List, Dict, Any, Optional, Callable
import inspect
import sys
from rich.console import Console
from rich.theme import Theme


# =============================================
# CORE PARAMETER SOURCES
# =============================================

class ParamSource:
    """Base class for parameter sources"""
    pass

class INPUT(ParamSource):
    def __init__(self, default=None, placeholder=None):
        self.default = default
        self.placeholder = placeholder

class MENU(ParamSource):
    def __init__(self, options, default=None):
        self.options = options  # [(label, value), ...] or [value, ...]
        self.default = default

class CONTEXT(ParamSource):
    def __init__(self, key):
        self.key = key


# =============================================
# CORE OUTPUT DESTINATIONS
# =============================================

class OutputDestination:
    """Base class for output destinations"""
    pass

class DISPLAY(OutputDestination):
    def __init__(self, format=None):
        self.format = format or "{value}"

class CONTEXT_OUT(OutputDestination):
    def __init__(self, key):
        self.key = key


# =============================================
# CLI CUSTOMIZATION CLASSES
# =============================================

class CLIFlowConfig:
    """CLI flow control configuration"""
    def __init__(self, type="sequential", save_result=False, history=False):
        self.type = type                    # "sequential", "parallel"
        self.save_result = save_result      # Save result to context
        self.history = history              # Keep command history

class CLILayoutConfig:
    """CLI layout configuration"""
    def __init__(self, style="default", show_help=True, show_types=False):
        self.style = style                  # "default", "compact", "verbose"
        self.show_help = show_help          # Show parameter descriptions
        self.show_types = show_types        # Show parameter types

class CLIPromptConfig:
    """CLI prompt configuration"""
    def __init__(self, prefix="> ", continuation="... ", error_prefix="Error: "):
        self.prefix = prefix                # Main prompt prefix
        self.continuation = continuation    # Continuation prompt
        self.error_prefix = error_prefix    # Error message prefix

class CLIGlobalConfig:
    """Global CLI configuration"""
    def __init__(self, title=None, theme="default", colors=True, 
                 exit_commands=None, help_command="help"):
        self.title = title                  # CLI title/banner
        self.theme = theme                  # "default", "minimal", "colorful"
        self.colors = colors                # Enable colors
        self.exit_commands = exit_commands or ["exit", "quit", "q"]
        self.help_command = help_command    # Help command name

class CLIFunctionCustomization:
    """Per-function CLI customization"""
    def __init__(self, flow=None, layout=None, prompt=None, aliases=None):
        self.flow = flow or CLIFlowConfig()
        self.layout = layout or CLILayoutConfig()
        self.prompt = prompt or CLIPromptConfig()
        self.aliases = aliases or []        # Command aliases


# =============================================
# BRIDGE CORE CLASSES
# =============================================

class FunctionMetadata:
    """Metadata for a registered function"""
    def __init__(self, func, name=None, description=None, params=None, output=None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or f"Execute {self.name}"
        self.params = params or {}
        self.output = output or DISPLAY()
        
        # Auto-extract parameter info from function signature
        self._extract_param_info()
    
    def _extract_param_info(self):
        """Extract parameter info from function signature"""
        sig = inspect.signature(self.func)
        for param_name, param in sig.parameters.items():
            if param_name not in self.params:
                # Auto-create INPUT source for basic types
                default = param.default if param.default != inspect.Parameter.empty else None
                self.params[param_name] = INPUT(default=default)

class Bridge:
    """Core bridge class"""
    def __init__(self, name, version="1.0.0"):
        self.name = name
        self.version = version
        self.functions = {}
        self.context = {}  # Shared context between function calls
    
    def register(self, func, name=None, description=None, params=None, output=None):
        """Register a function with the bridge"""
        metadata = FunctionMetadata(func, name, description, params, output)
        self.functions[metadata.name] = metadata
        return metadata


# =============================================
# CLI INTERFACE IMPLEMENTATION
# =============================================

class Interface:
    """Base interface class for bridge"""
    
    def __init__(self, bridge: Bridge):
        self.bridge = bridge
    
    def customize(self, config: Dict[str, Any]):
        """Customize interface (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def run(self):
        """Run the interface (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement this method")

class CLI(Interface):
    """CLI interface for bridge"""
    
    def __init__(self, bridge: Bridge):
        self.bridge = bridge
        self.customizations = {}
        self.global_config = CLIGlobalConfig()
        self.running = False
        self.console = Console(theme=Theme({
            "banner": "bold cyan",
            "command": "bold yellow",
            "error": "bold red",
            "help": "green",
            "result": "bold magenta"
        }))
    
    def customize(self, config: Dict[str, Any]):
        """Customize CLI interface"""
        for key, value in config.items():
            if key == "global":
                # Update global config
                if isinstance(value, dict):
                    for attr, attr_value in value.items():
                        if hasattr(self.global_config, attr):
                            setattr(self.global_config, attr, attr_value)
                elif isinstance(value, CLIGlobalConfig):
                    self.global_config = value
            else:
                # Function-specific customization
                if isinstance(value, dict):
                    # Convert dict to CLIFunctionCustomization
                    flow_config = CLIFlowConfig(**value.get('flow', {})) if 'flow' in value else CLIFlowConfig()
                    layout_config = CLILayoutConfig(**value.get('layout', {})) if 'layout' in value else CLILayoutConfig()
                    prompt_config = CLIPromptConfig(**value.get('prompt', {})) if 'prompt' in value else CLIPromptConfig()
                    
                    # Handle direct properties
                    for prop in ['save_result', 'history']:
                        if prop in value:
                            setattr(flow_config, prop, value[prop])
                    
                    self.customizations[key] = CLIFunctionCustomization(
                        flow=flow_config,
                        layout=layout_config, 
                        prompt=prompt_config,
                        aliases=value.get('aliases', [])
                    )
                elif isinstance(value, CLIFunctionCustomization):
                    self.customizations[key] = value
    
    def run(self):
        """Run the CLI interface"""
        self.running = True
        
        # Show title/banner
        if self.global_config.title:
            if self.global_config.colors:
                self.console.print(f"\n{self.global_config.title}", style="banner")
                self.console.print("=" * len(self.global_config.title), style="banner")
            else:
                print(f"\n{self.global_config.title}")
                print("=" * len(self.global_config.title))
        
        if self.global_config.colors:
            self.console.print(f"\n{self.bridge.name} CLI v{self.bridge.version}", style="banner")
            self.console.print("Type 'help' for available commands or 'exit' to quit.\n", style="help")
        else:
            print(f"\n{self.bridge.name} CLI v{self.bridge.version}")
            print("Type 'help' for available commands or 'exit' to quit.\n")
        
        while self.running:
            try:
                prompt = (self.global_config.title or self.bridge.name) + " > "
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                # Handle exit commands
                if command.lower() in self.global_config.exit_commands:
                    if self.global_config.colors:
                        self.console.print("Goodbye!", style="banner")
                    else:
                        print("Goodbye!")
                    break
                
                # Handle help command
                if command.lower() == self.global_config.help_command:
                    self._show_help()
                    continue
                
                # Parse and execute command
                self._execute_command(command)
                
            except KeyboardInterrupt:
                if self.global_config.colors:
                    self.console.print("\nGoodbye!", style="banner")
                else:
                    print("\nGoodbye!")
                break
            except Exception as e:
                if self.global_config.colors:
                    self.console.print(f"Error: {e}", style="error")
                else:
                    print(f"Error: {e}")
    
    def _show_help(self):
        """Show help information"""
        if self.global_config.colors:
            self.console.print("\nAvailable commands:", style="help")
            self.console.print("-" * 20, style="help")
        else:
            print("\nAvailable commands:")
            print("-" * 20)
        
        for name, metadata in self.bridge.functions.items():
            # Show aliases if any
            custom = self.customizations.get(name)
            aliases = f" (aliases: {', '.join(custom.aliases)})" if custom and custom.aliases else ""
            if self.global_config.colors:
                self.console.print(f"  {name}{aliases}", style="command")
                if custom and custom.layout.show_help:
                    self.console.print(f"    {metadata.description}", style="help")
            else:
                print(f"  {name}{aliases}")
                if custom and custom.layout.show_help:
                    print(f"    {metadata.description}")
        if self.global_config.colors:
            self.console.print(f"\n  {self.global_config.help_command} - Show this help", style="help")
            self.console.print(f"  {'/'.join(self.global_config.exit_commands)} - Exit", style="help")
            self.console.print()
        else:
            print(f"\n  {self.global_config.help_command} - Show this help")
            print(f"  {'/'.join(self.global_config.exit_commands)} - Exit")
            print()
    
    def _execute_command(self, command: str):
        """Execute a command"""
        parts = command.split()
        cmd_name = parts[0]
        args = parts[1:]
        
        # Find function (including aliases)
        func_name = self._resolve_function_name(cmd_name)
        if not func_name:
            print(f"Unknown command: {cmd_name}")
            return
        
        metadata = self.bridge.functions[func_name]
        custom = self.customizations.get(func_name, CLIFunctionCustomization())
        
        try:
            # Collect parameters based on flow type
            if custom.flow.type == "sequential":
                params = self._collect_params_sequential(metadata, custom, args)
            else:  # parallel
                params = self._collect_params_parallel(metadata, custom, args)
            
            # Execute function
            result = metadata.func(**params)
            
            # Handle output
            self._handle_output(result, metadata.output, custom)
            
            # Save to context if configured
            if custom.flow.save_result:
                self.bridge.context['last_result'] = result
            
        except Exception as e:
            print(f"{custom.prompt.error_prefix}{e}")
    
    def _resolve_function_name(self, cmd_name: str) -> Optional[str]:
        """Resolve command name including aliases"""
        # Direct match
        if cmd_name in self.bridge.functions:
            return cmd_name
        
        # Check aliases
        for func_name, custom in self.customizations.items():
            if cmd_name in custom.aliases:
                return func_name
        
        return None
    
    def _collect_params_sequential(self, metadata: FunctionMetadata, 
                                 custom: CLIFunctionCustomization, args: List[str]) -> Dict[str, Any]:
        """Collect parameters sequentially (one at a time)"""
        params = {}
        arg_index = 0
        
        for param_name, param_source in metadata.params.items():
            if arg_index < len(args):
                # Use provided argument
                value = args[arg_index]
                arg_index += 1
            else:
                # Prompt for parameter
                value = self._prompt_for_param(param_name, param_source, custom)
            
            params[param_name] = self._convert_param_value(value, param_source)
        
        return params
    
    def _collect_params_parallel(self, metadata: FunctionMetadata,
                                custom: CLIFunctionCustomization, args: List[str]) -> Dict[str, Any]:
        """Collect parameters in parallel (show all at once)"""
        raise TypeError("'parallel' flow is not supported in CLI mode.")
    
    def _prompt_for_param(self, param_name: str, param_source: ParamSource,
                         custom: CLIFunctionCustomization) -> str:
        """Prompt user for a parameter value"""
        if isinstance(param_source, INPUT):
            prompt = f"{param_name}"
            if param_source.placeholder:
                prompt += f" ({param_source.placeholder})"
            if param_source.default is not None:
                prompt += f" [{param_source.default}]"
            prompt += ": "
            
            value = input(prompt).strip()
            return value if value else (param_source.default or "")
        
        elif isinstance(param_source, MENU):
            print(f"\n{param_name} options:")
            
            # Normalize options to (label, value) tuples
            options = []
            for i, option in enumerate(param_source.options):
                if isinstance(option, tuple):
                    label, value = option
                else:
                    label, value = str(option), option
                options.append((label, value))
                print(f"  {i + 1}. {label}")
            
            while True:
                try:
                    choice = input(f"\nSelect {param_name} (1-{len(options)}): ").strip()
                    if not choice and param_source.default is not None:
                        return param_source.default
                    
                    index = int(choice) - 1
                    if 0 <= index < len(options):
                        return options[index][1]
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a number.")
        
        elif isinstance(param_source, CONTEXT):
            return self.bridge.context.get(param_source.key, "")
        
        return ""
    
    def _convert_param_value(self, value: str, param_source: ParamSource) -> Any:
        """Convert string input to appropriate type"""
        if not value:
            return None
        
        # Handle MENU with enum values
        if isinstance(param_source, MENU):
            # Try to detect if options are enum values
            options = param_source.options
            # Normalize options to (label, value) tuples
            normalized = []
            for option in options:
                if isinstance(option, tuple):
                    label, val = option
                else:
                    label, val = str(option), option
                normalized.append((label, val))
            # If value is already the correct type, return it
            for label, val in normalized:
                if str(value) == str(val) or str(value) == label:
                    return val
            # Try to convert by index (1-based)
            try:
                idx = int(value) - 1
                if 0 <= idx < len(normalized):
                    return normalized[idx][1]
            except Exception:
                pass
            return value  # fallback

        # Try to convert to number if it looks like one
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _handle_output(self, result: Any, output: OutputDestination, 
                      custom: CLIFunctionCustomization):
        """Handle function output"""
        if isinstance(output, DISPLAY):
            formatted = output.format.format(value=result)
            if self.global_config.colors:
                self.console.print(f"\n{formatted}", style="result")
            else:
                print(f"\n{formatted}")
        elif isinstance(output, CONTEXT_OUT):
            self.bridge.context[output.key] = result
            if self.global_config.colors:
                self.console.print(f"\nResult saved to context: {output.key}", style="result")
            else:
                print(f"\nResult saved to context: {output.key}")


# =============================================
# USAGE EXAMPLE
# =============================================

if __name__ == "__main__":
    # Example usage
    class Operation(IntEnum):
        ADD = 0
        SUBTRACT = 1
        MULTIPLY = 2
        DIVIDE = 3

    def calculate(a: float, b: float, operation: Operation) -> float:
        """Calculate two numbers using the specified operation"""
        ops = {
            Operation.ADD: lambda x, y: x + y,
            Operation.SUBTRACT: lambda x, y: x - y,
            Operation.MULTIPLY: lambda x, y: x * y,
            Operation.DIVIDE: lambda x, y: x / y if y != 0 else None
        }
        return ops[operation](a, b)

    # Create bridge and register function
    bridge = Bridge("Calculator")
    bridge.register(
        calculate,
        params={
            "a": INPUT(default=0, placeholder="First number"),
            "b": INPUT(default=0, placeholder="Second number"),
            "operation": MENU([
                ("Add", Operation.ADD),
                ("Subtract", Operation.SUBTRACT),
                ("Multiply", Operation.MULTIPLY),
                ("Divide", Operation.DIVIDE)
            ], default=Operation.ADD)
        },
        output=DISPLAY(format="Result: {value}")
    )

    # Create and customize CLI
    cli = CLI(bridge)
    cli.customize({
        "calculate": {
            "flow": {"type": "sequential", "save_result": True, "history": True},
            "layout": {"show_help": True, "show_types": False},
            "aliases": ["calc", "c"]
        },
        "global": {
            "title": "Calculator CLI",
            "theme": "default",
            "colors": True
        }
    })

    # Run CLI
    cli.run()