"""
bridges.core.types
------------------
Minimal concrete parameter and output types for bridges core.
"""
from .base import ParamSource, OutputDestination
from typing import Any, List

class InputParamSource(ParamSource):
    """
    Parameter source for direct user input.

    :param default: Default value for the parameter.
    :param placeholder: Placeholder text for prompts.
    """
    def __init__(self, default: Any = None, placeholder: str = None):
        self.default = default
        self.placeholder = placeholder

class MenuParamSource(ParamSource):
    """
    Parameter source for menu/option selection.

    :param options: List of selectable options.
    :param default: Default selected value.
    """
    def __init__(self, options: List[Any], default: Any = None):
        self.options = options
        self.default = default

class ContextParamSource(ParamSource):
    """
    Parameter source from context.

    :param key: Context key to retrieve value from.
    """
    def __init__(self, key: str):
        self.key = key

class DisplayOutputDestination(OutputDestination):
    """
    Output destination for displaying results.

    :param format: Format string for displaying the value.
    """
    def __init__(self, format: str = "{value}"):
        self.format = format

class ContextOutputDestination(OutputDestination):
    """
    Output destination for saving results to context.

    :param key: Context key to save the result under.
    """
    def __init__(self, key: str):
        self.key = key
