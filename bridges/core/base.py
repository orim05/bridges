"""
bridges.core.base
Abstract base classes and minimal core types for bridges framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ParamSource(ABC):
    """
    Base class for parameter sources.
    """

    pass


class OutputDestination(ABC):
    """
    Base class for output destinations.
    """

    pass


class IBridge(ABC):
    """
    Abstract base class for a Bridge (for type hinting and interface).
    """

    pass


class BridgeInterface(ABC):
    """
    Abstract interface for bridge UIs (CLI, Web, etc).

    :param bridge: An instance of a bridge to be used by the interface.
    """

    def __init__(self, bridge):
        self.bridge = bridge

    @abstractmethod
    def customize(self, config: Dict[str, Any]):
        """
        Customize the interface with the given configuration.

        :param config: Dictionary of configuration options.
        """
        if hasattr(self, "config") and isinstance(self.config, dict):
            self.config.update(config)

    @abstractmethod
    def run(self):
        """
        Run the interface.
        """
        pass
