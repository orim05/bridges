"""
bridges.core.errors

Custom exception classes for error management in the bridges framework.
"""


class BridgeValidationError(Exception):
    """Raised when parameter validation fails in a bridge function."""

    pass


class BridgeExecutionError(Exception):
    """Raised when execution of a bridge function fails."""

    pass


class ContextKeyError(Exception):
    """Raised when a required key is missing from the bridge context."""

    pass
