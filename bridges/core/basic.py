"""
bridges.core.basic
Minimal implementation of the core bridge and function registration.
"""
import inspect
from typing import Any, Callable, Dict, Optional
from .types import InputParamSource

class FunctionMetadata:
    """
    Metadata for a registered function.
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        output: Any = None,
    ):
        """
        :param func: The function object.
        :param name: Optional name for the function.
        :param description: Optional description.
        :param params: Parameter sources.
        :param output: Output destination.
        """
        
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or f"Execute {self.name}"
        if params is not None:
            self.params = params
        else:
            self.params = {}
            sig = inspect.signature(func)
            for pname, param in sig.parameters.items():
                default = param.default if param.default != inspect.Parameter.empty else None
                self.params[pname] = InputParamSource(default=default)
        self.output = output


class Bridge:
    """
    Minimal core bridge class for registering functions and holding context.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        """
        :param name: Name of the bridge.
        :param version: Version string.
        """
        self.name = name
        self.version = version
        self.functions: Dict[str, FunctionMetadata] = {}
        self.context: Dict[str, Any] = {}

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        output: Any = None,
    ) -> FunctionMetadata:
        """
        Register a function with the bridge.

        :param func: The function to register.
        :param name: Optional name.
        :param description: Optional description.
        :param params: Optional parameter sources.
        :param output: Optional output destination.
        :return: FunctionMetadata instance.
        """
        metadata = FunctionMetadata(func, name, description, params, output)
        self.functions[metadata.name] = metadata
        return metadata
