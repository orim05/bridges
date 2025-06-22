"""
bridges.interfaces

Simple interface implementations for the bridges framework.
"""

from .cli import CLI

# Backward compatibility alias
SimpleCLI = CLI

__all__ = ["CLI", "SimpleCLI"]
