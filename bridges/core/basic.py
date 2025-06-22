"""
bridges.core.basic

Core bridge functionality for registering functions, managing context, and event hooks.
"""

import copy
import inspect
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ValidationError, create_model

from .errors import BridgeExecutionError, BridgeValidationError
from .types import ParamSource


class FunctionMetadata:
    """
    Metadata for a registered function, including parameter sources, output destinations, and validation.
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        output: Any = None,
        debug: bool = False,
    ):
        """
        :param func: The function object.
        :param name: Optional name for the function.
        :param description: Optional description.
        :param params: Parameter sources or metadata.
        :param output: Output destination or list of destinations.
        :param debug: Debug flag for logging.
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or (
            func.__doc__.strip() if func.__doc__ else f"Execute {self.name}"
        )
        self.debug = debug
        # Parameter extraction and metadata
        if params is not None:
            self.params = {}
            for pname, pval in params.items():
                if hasattr(pval, "validator"):  # Check if it's ParameterMetadata
                    self.params[pname] = pval
                else:
                    self.params[pname] = pval
        else:
            self.params = {}
            sig = inspect.signature(func)
            for pname, param in sig.parameters.items():
                annotation = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else None
                )
                for source_cls in ParamSource.__subclasses__():
                    if source_cls.supports(annotation, param):
                        meta = None
                        if hasattr(param, "metadata") and param.metadata:
                            meta = param.metadata
                        self.params[pname] = source_cls.from_param(
                            annotation, param, meta
                        )
                        break
        # Output destinations
        if output is None:
            self.output = []
        elif hasattr(output, "__iter__") and not hasattr(
            output, "strip"
        ):  # Check if it's a list-like object
            self.output = output
        else:
            self.output = [output]
        self.pydantic_model = self._make_pydantic_model(func)

    def _make_pydantic_model(self, func: Callable) -> BaseModel:
        sig = inspect.signature(func)
        fields = {}
        for name, param in sig.parameters.items():
            annotation = (
                param.annotation if param.annotation != inspect.Parameter.empty else str
            )
            default = param.default if param.default != inspect.Parameter.empty else ...
            fields[name] = (annotation, default)
        return create_model(f"{func.__name__}Model", **fields)

    def __call__(self, params: dict) -> Any:
        """
        Validate and coerce parameters using the Pydantic model, then call the function.
        Calls pre, post, and error hooks as registered on the bridge.
        :param params: Dictionary of raw parameter values.
        :return: Result of the function call with validated parameters.
        :raises BridgeValidationError: If parameter validation fails.
        :raises BridgeExecutionError: If function execution fails.
        """
        bridge = getattr(self, "bridge", None)
        if getattr(self, "debug", False) or (
            bridge and getattr(bridge, "debug", False)
        ):
            print(f"[DEBUG] Calling {self.name} with params: {params}")
        if bridge and hasattr(bridge, "_pre_hooks"):
            for hook in bridge._pre_hooks:
                hook(params, self)
        # Custom per-parameter validation
        for pname, meta in getattr(self, "params", {}).items():
            if hasattr(meta, "validator") and meta.validator:
                value = params.get(pname, meta.default)
                try:
                    if not meta.validator(value):
                        raise BridgeValidationError(
                            f"Validation failed for parameter '{pname}': value={value} (custom validator returned False)"
                        )
                except Exception as e:
                    raise BridgeValidationError(
                        f"Validation error for parameter '{pname}': value={value} ({e})"
                    )
        try:
            validated = self.pydantic_model(**params)
        except ValidationError as e:
            if bridge and hasattr(bridge, "_error_hooks"):
                for hook in bridge._error_hooks:
                    hook(e, self)
            msg = f"Parameter validation failed for function '{self.name}': {e}"
            if getattr(self, "debug", False) or (
                bridge and getattr(bridge, "debug", False)
            ):
                print(f"[DEBUG] {msg}")
            raise BridgeValidationError(msg) from e
        try:
            result = self.func(**validated.model_dump())
        except Exception as e:
            if bridge and hasattr(bridge, "_error_hooks"):
                for hook in bridge._error_hooks:
                    hook(e, self)
            msg = f"Execution failed for function '{self.name}': {e}"
            if getattr(self, "debug", False) or (
                bridge and getattr(bridge, "debug", False)
            ):
                print(f"[DEBUG] {msg}")
            raise BridgeExecutionError(msg) from e
        if bridge and hasattr(bridge, "_post_hooks"):
            for hook in bridge._post_hooks:
                hook(result, self)
        return result

    validate_and_call = __call__


class Bridge:
    """
    Core bridge class for registering functions, managing context, and event hooks.
    """

    def __init__(self, name: str, version: str = "1.0.0", debug: bool = False):
        """
        :param name: Name of the bridge.
        :param version: Version string.
        :param debug: Debug flag for logging.
        """
        self.name = name
        self.version = version
        self.functions: Dict[str, FunctionMetadata] = {}
        self.context: Dict[str, Any] = {}
        self.context_history: List[Dict[str, Any]] = [copy.deepcopy(self.context)]
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
        self._error_hooks: List[Callable] = []
        self.debug = debug

    def add_pre_hook(self, hook: Callable) -> None:
        """Register a pre-execution hook. Called with (params, meta) before function execution."""
        self._pre_hooks.append(hook)

    def add_post_hook(self, hook: Callable) -> None:
        """Register a post-execution hook. Called with (result, meta) after function execution."""
        self._post_hooks.append(hook)

    def add_error_hook(self, hook: Callable) -> None:
        """Register an error hook. Called with (exception, meta) if an error occurs."""
        self._error_hooks.append(hook)

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
        :param params: Optional parameter sources or metadata.
        :param output: Optional output destination(s).
        :return: FunctionMetadata instance.
        """
        metadata = FunctionMetadata(func, name, description, params, output)
        metadata.bridge = self  # Attach bridge reference for hooks
        self.functions[metadata.name] = metadata
        return metadata

    def update_context(self, key: str, value: Any) -> None:
        """
        Update the context and snapshot the new state in history.
        """
        self.context[key] = value
        self.context_history.append(copy.deepcopy(self.context))

    def clear_context(self) -> None:
        """
        Clear the context and reset history.
        """
        self.context.clear()
        self.context_history = [copy.deepcopy(self.context)]

    def restore_context(self, index: int) -> None:
        """
        Restore the context to a previous state from history.
        :param index: Index in the context history list.
        """
        if 0 <= index < len(self.context_history):
            self.context = copy.deepcopy(self.context_history[index])
            self.context_history.append(copy.deepcopy(self.context))
        else:
            raise IndexError("Invalid context history index.")

    def get_context_history(self) -> List[Dict[str, Any]]:
        """
        Get the list of context history snapshots.
        :return: List of context dicts.
        """
        return self.context_history
