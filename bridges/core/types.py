"""
bridges.core.types
Minimal concrete parameter and output types for bridges core.
"""

import inspect
from abc import ABC
from typing import Any, List, Optional, Type

from .base import OutputDestination, ParamSource


class ParamSource(ABC):
    """
    Base class for parameter sources. Subclasses should implement supports and from_param for extensible parameter handling.
    """

    @classmethod
    def supports(
        cls: Type["ParamSource"], annotation: Any, param: inspect.Parameter
    ) -> bool:
        """
        Return True if this ParamSource can handle the given annotation/param.
        :param annotation: The type annotation of the parameter.
        :param param: The inspect.Parameter object.
        """
        return False

    @classmethod
    def from_param(
        cls: Type["ParamSource"],
        annotation: Any,
        param: inspect.Parameter,
        metadata: Optional[Any] = None,
    ) -> "ParamSource":
        """
        Construct a ParamSource instance for the given annotation/param.
        :param annotation: The type annotation of the parameter.
        :param param: The inspect.Parameter object.
        :param metadata: Optional metadata for the parameter.
        """
        return cls()


class InputParamSource(ParamSource):
    """
    Parameter source for direct user input.
    """

    def __init__(
        self,
        default: Any = None,
        placeholder: Optional[str] = None,
        description: Optional[str] = None,
        validator: Optional[Any] = None,
    ):
        """
        :param default: Default value for the parameter.
        :param placeholder: Placeholder text for prompts.
        :param description: Description for the parameter.
        :param validator: Callable for custom validation (value -> bool or raises).
        """
        self.default: Any = default
        self.placeholder: Optional[str] = placeholder
        self.description: Optional[str] = description
        self.validator: Optional[Any] = validator

    @classmethod
    def supports(
        cls: Type["InputParamSource"], annotation: Any, param: inspect.Parameter
    ) -> bool:
        """
        Accepts any parameter not handled by other sources.
        """
        return True

    @classmethod
    def from_param(
        cls: Type["InputParamSource"],
        annotation: Any,
        param: inspect.Parameter,
        metadata: Optional[Any] = None,
    ) -> "InputParamSource":
        """
        Create an InputParamSource from a parameter.
        """
        default = param.default if param.default != inspect.Parameter.empty else None
        description = getattr(metadata, "description", None) if metadata else None
        validator = getattr(metadata, "validator", None) if metadata else None
        return cls(default=default, description=description, validator=validator)


class MenuParamSource(ParamSource):
    """
    Parameter source for menu/option selection.
    """

    def __init__(
        self,
        options: list,
        default: Any = None,
        description: Optional[str] = None,
        validator: Optional[Any] = None,
    ):
        """
        :param options: List of selectable options. Each option can be a value or a (label, value) tuple.
        :param default: Default selected value.
        :param description: Description for the parameter.
        :param validator: Callable for custom validation (value -> bool or raises).
        """
        # Normalize options to (label, value) tuples
        normalized: list = []
        for option in options:
            if hasattr(option, "__len__") and len(option) == 2:
                label, value = option
            else:
                label, value = str(option), option
            normalized.append((label, value))
        self.options: list = normalized
        self.default: Any = default
        self.description: Optional[str] = description
        self.validator: Optional[Any] = validator

    @classmethod
    def supports(
        cls: Type["MenuParamSource"], annotation: Any, param: inspect.Parameter
    ) -> bool:
        """
        Supports Enum-annotated parameters by providing a menu of enum values.
        """
        from enum import Enum

        return (
            annotation
            and hasattr(annotation, "__class__")
            and issubclass(annotation, Enum)
        )

    @classmethod
    def from_param(
        cls: Type["MenuParamSource"],
        annotation: Any,
        param: inspect.Parameter,
        metadata: Optional[Any] = None,
    ) -> "MenuParamSource":
        """
        Create a MenuParamSource from an Enum-annotated parameter.
        """
        options = [(e.name, e) for e in annotation]
        default = param.default if param.default != inspect.Parameter.empty else None
        description = getattr(metadata, "description", None) if metadata else None
        validator = getattr(metadata, "validator", None) if metadata else None
        return cls(
            options, default=default, description=description, validator=validator
        )


class ContextParamSource(ParamSource):
    """
    Parameter source from context.
    """

    def __init__(self, key: str):
        """
        :param key: Context key to retrieve value from.
        """
        self.key: str = key

    @classmethod
    def supports(
        cls: Type["ContextParamSource"], annotation: Any, param: inspect.Parameter
    ) -> bool:
        """
        Returns True if this source should handle the parameter (extend for custom logic).
        """
        # Could be extended to support a special annotation or marker
        return False

    @classmethod
    def from_param(
        cls: Type["ContextParamSource"],
        annotation: Any,
        param: inspect.Parameter,
        metadata: Optional[Any] = None,
    ) -> Optional["ContextParamSource"]:
        """
        Create a ContextParamSource from a parameter (extend for custom logic).
        """
        return None


class DisplayOutputDestination(OutputDestination):
    """
    Output destination for displaying results.
    """

    def __init__(self, format: str = "{value}"):
        """
        :param format: Format string for displaying the value.
        """
        self.format: str = format


class ContextOutputDestination(OutputDestination):
    """
    Output destination for saving results to context.
    """

    def __init__(self, key: str):
        """
        :param key: Context key to save the result under.
        """
        self.key: str = key


class ListParamSource(ParamSource):
    """
    Parameter source for a list of values (multi-value input).
    """

    def __init__(
        self,
        separator: str = ",",
        default: Optional[list] = None,
        description: Optional[str] = None,
        element_type: type = str,
        validator: Optional[Any] = None,
    ):
        """
        :param separator: Separator for input values (default: ',').
        :param default: Default list value.
        :param description: Description for the parameter.
        :param element_type: Type of each element in the list (default: str).
        :param validator: Callable for custom validation (value -> bool or raises).
        """
        self.separator: str = separator
        self.default: list = default or []
        self.description: Optional[str] = description
        self.element_type: type = element_type
        self.validator: Optional[Any] = validator

    @classmethod
    def supports(
        cls: Type["ListParamSource"], annotation: Any, param: inspect.Parameter
    ) -> bool:
        from typing import get_origin

        return (
            annotation is list
            or annotation is List[Any]
            or (get_origin(annotation) in (list, List))
        )

    @classmethod
    def from_param(
        cls: Type["ListParamSource"],
        annotation: Any,
        param: inspect.Parameter,
        metadata: Optional[Any] = None,
    ) -> "ListParamSource":
        from typing import get_args

        separator = ","
        default = None
        description = getattr(metadata, "description", None) if metadata else None
        validator = getattr(metadata, "validator", None) if metadata else None
        element_type = str
        if hasattr(annotation, "__args__") and annotation.__args__:
            element_type = annotation.__args__[0]
        elif hasattr(annotation, "__origin__") and annotation.__origin__ in (
            list,
            List,
        ):
            args = get_args(annotation)
            if args:
                element_type = args[0]
        return cls(
            separator=separator,
            default=default,
            description=description,
            element_type=element_type,
            validator=validator,
        )


class FileParamSource(ParamSource):
    """
    Parameter source for file input (reads file content as parameter value).
    """

    def __init__(
        self,
        mode: str = "r",
        description: Optional[str] = None,
        validator: Optional[Any] = None,
    ):
        """
        :param mode: File open mode (default: 'r').
        :param description: Description for the parameter.
        :param validator: Callable for custom validation (value -> bool or raises).
        """
        self.mode: str = mode
        self.description: Optional[str] = description
        self.validator: Optional[Any] = validator

    @classmethod
    def supports(
        cls: Type["FileParamSource"], annotation: Any, param: inspect.Parameter
    ) -> bool:
        return annotation == "file" or (
            hasattr(annotation, "__name__") and annotation.__name__ == "TextIO"
        )

    @classmethod
    def from_param(
        cls: Type["FileParamSource"],
        annotation: Any,
        param: inspect.Parameter,
        metadata: Optional[Any] = None,
    ) -> Optional["FileParamSource"]:
        mode = "r"
        description = getattr(metadata, "description", None) if metadata else None
        validator = getattr(metadata, "validator", None) if metadata else None
        return cls(mode=mode, description=description, validator=validator)


class FileOutputDestination(OutputDestination):
    """
    Output destination for writing results to a file.
    """

    def __init__(
        self, path_param: str, mode: str = "w", description: Optional[str] = None
    ):
        """
        :param path_param: Name of the parameter that provides the file path.
        :param mode: File open mode (default: 'w').
        :param description: Description for the output.
        """
        self.path_param: str = path_param
        self.mode: str = mode
        self.description: Optional[str] = description


class ParameterMetadata:
    """
    Metadata for a function parameter, including description, required, default, and validator.
    """

    def __init__(
        self,
        description: Optional[str] = None,
        required: bool = True,
        default: Any = None,
        validator: Optional[Any] = None,
    ):
        """
        :param description: Description for the parameter.
        :param required: Whether the parameter is required.
        :param default: Default value for the parameter.
        :param validator: Callable for custom validation (value -> bool or raises).
        """
        self.description: Optional[str] = description
        self.required: bool = required
        self.default: Any = default
        self.validator: Optional[Any] = validator
