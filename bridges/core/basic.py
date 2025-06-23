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

try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None


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
        Initialize FunctionMetadata for a registered function.
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
        """
        Create a Pydantic model for parameter validation based on the function signature.
        :param func: The function to create a model for.
        :return: A dynamically created Pydantic model class.
        """
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
        self._debug_print_call(params, bridge)
        self._run_pre_hooks(params, bridge)
        self._resolve_callable_defaults(params)
        self._run_param_validators(params)
        validated = self._validate_params(params, bridge)
        result = self._execute_function(validated, bridge)
        self._handle_output_destinations(result, bridge)
        self._run_post_hooks(result, bridge)
        return result

    def _debug_print_call(self, params, bridge):
        """
        Print debug information about the function call if debug is enabled.
        :param params: Parameters passed to the function.
        :param bridge: The bridge instance (may be None).
        """
        if getattr(self, "debug", False) or (
            bridge and getattr(bridge, "debug", False)
        ):
            print(f"[DEBUG] Calling {self.name} with params: {params}")

    def _run_pre_hooks(self, params, bridge):
        """
        Run all registered pre-execution hooks before function execution.
        :param params: Parameters passed to the function.
        :param bridge: The bridge instance (may be None).
        """
        if bridge and hasattr(bridge, "_pre_hooks"):
            for hook in bridge._pre_hooks:
                hook(params, self)

    def _resolve_callable_defaults(self, params):
        """
        Resolve any callable defaults for missing parameters before validation.
        :param params: Parameters passed to the function.
        """
        for pname, meta in getattr(self, "params", {}).items():
            if pname not in params or params[pname] is None:
                default = getattr(meta, "default", None)
                if callable(default):
                    params[pname] = default()

    def _run_param_validators(self, params):
        """
        Run custom per-parameter validators, raising BridgeValidationError on failure.
        :param params: Parameters passed to the function.
        """
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

    def _validate_params(self, params, bridge):
        """
        Validate and coerce parameters using the Pydantic model, raising BridgeValidationError on failure.
        :param params: Parameters passed to the function.
        :param bridge: The bridge instance (may be None).
        :return: Validated Pydantic model instance.
        :raises BridgeValidationError: If validation fails.
        """
        try:
            return self.pydantic_model(**params)
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

    def _execute_function(self, validated, bridge):
        """
        Call the registered function with validated parameters, handling errors and hooks.
        :param validated: Validated Pydantic model instance.
        :param bridge: The bridge instance (may be None).
        :return: The result of the function call.
        :raises BridgeExecutionError: If function execution fails.
        """
        try:
            return self.func(**validated.model_dump())
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

    def _handle_output_destinations(self, result, bridge):
        """
        Send the function result to all registered output destinations (e.g., display, context).
        :param result: The result of the function call.
        :param bridge: The bridge instance (may be None).
        """
        if bridge and hasattr(self, "output"):
            for dest in self.output:
                if hasattr(dest, "send") and callable(getattr(dest, "send")):
                    dest.send(result, bridge)

    def _run_post_hooks(self, result, bridge):
        """
        Run all registered post-execution hooks after function execution.
        :param result: The result of the function call.
        :param bridge: The bridge instance (may be None).
        """
        if bridge and hasattr(bridge, "_post_hooks"):
            for hook in bridge._post_hooks:
                hook(result, self)

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

    def register_class(
        self,
        cls,
        params: Optional[Dict[str, Any]] = None,
        output: Any = None,
        methods: Optional[list] = None,
        stateless: bool = False,
        context_key: str = None,
    ):
        """
        Register a class and its methods as bridge functions.
        If stateless, registers static/class methods as independent functions.
        If stateful, registers a constructor and instance methods that operate on the stored instance.
        :param cls: The class to register.
        :param params: Constructor parameters (for stateful).
        :param output: Output destinations for constructor (for stateful).
        :param methods: List of method dicts: {"name", "params", "output", "description"}.
        :param stateless: If True, treat all methods as static/class methods.
        :param context_key: Key to store/retrieve the instance in context (for stateful).
        """
        if stateless:
            self._register_stateless_class_methods(cls, methods)
        else:
            key = context_key or f"{cls.__name__}_instance"
            self._register_stateful_constructor(cls, params, output, key)
            self._register_stateful_methods(cls, methods, key)

    def _register_stateless_class_methods(self, cls, methods):
        """Register static/class methods as independent bridge functions."""
        for method in methods or []:
            method_name = method["name"]
            func = getattr(cls, method_name)
            self.register(
                func,
                name=f"{cls.__name__}.{method_name}",
                description=method.get("description"),
                params=method.get("params"),
                output=method.get("output"),
            )

    def _register_stateful_constructor(self, cls, params, output, key):
        """Register a constructor function that creates and stores the instance in context, supporting multiple named instances."""
        import inspect

        def make_and_store_instance(*args, instance_name: str = None, **kwargs):
            instance = cls(*args, **kwargs)
            store_key = f"{key}:{instance_name}" if instance_name else key
            self.update_context(store_key, instance)
            return instance

        # Use the signature from __init__, excluding 'self'
        sig = inspect.signature(cls.__init__)
        params_list = list(sig.parameters.values())
        if params_list and params_list[0].name == "self":
            params_list = params_list[1:]
        params_list.append(
            inspect.Parameter(
                "instance_name",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=str,
            )
        )
        make_and_store_instance.__signature__ = inspect.Signature(params_list)
        self.register(
            make_and_store_instance,
            name=f"create_{cls.__name__.lower()}_instance",
            description=f"Create and store a {cls.__name__} instance in context. Optionally specify instance_name for multiple instances.",
            params=params,
            output=output,
        )

    def _register_stateful_methods(self, cls, methods, key):
        """Register instance methods that operate on the stored instance in context, supporting multiple named instances."""
        import inspect

        for method in methods or []:
            method_name = method["name"]

            def make_method_func(mname):
                method_obj = getattr(cls, mname)
                sig = inspect.signature(method_obj)
                # Remove 'self' from the signature
                params = list(sig.parameters.values())
                if params and params[0].name == "self":
                    params = params[1:]
                # Add instance_name as a keyword-only parameter
                params.append(
                    inspect.Parameter(
                        "instance_name",
                        inspect.Parameter.KEYWORD_ONLY,
                        default=None,
                        annotation=str,
                    )
                )
                new_sig = inspect.Signature(params)

                def method_func(*args, instance_name: str = None, **kwargs):
                    store_key = f"{key}:{instance_name}" if instance_name else key
                    instance = self.context.get(store_key)
                    if not instance:
                        raise RuntimeError(
                            f"No {cls.__name__} instance found in context for key '{store_key}'. Please create one first."
                        )
                    return getattr(instance, mname)(*args, **kwargs)

                method_func.__signature__ = new_sig
                return method_func

            self.register(
                make_method_func(method_name),
                name=f"{cls.__name__}.{method_name}",
                description=method.get("description"),
                params=method.get("params"),
                output=method.get("output"),
            )

    def list_all_instances(self):
        """
        Return a dictionary mapping each registered stateful class name to a list of all instance names (or keys) currently stored in context for that class.
        Example: { 'Counter': ['default', 'mycounter', ...], ... }
        """
        from collections import defaultdict

        result = defaultdict(list)
        for key in self.context:
            if "_instance" in key:
                # e.g., key = 'Counter_instance' or 'Counter_instance:myname'
                base, *rest = key.split(":", 1)
                class_part = base.replace("_instance", "")
                instance_name = rest[0] if rest else "default"
                result[class_part].append(instance_name)
        return dict(result)
