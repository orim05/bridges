"""
tests.test_cli_smoke
Smoke test for CLI instantiation.
"""

from bridges.core.basic import Bridge
from bridges.core.types import DisplayOutputDestination, InputParamSource
from bridges.interfaces.cli import CLI


def test_cli_instantiation():
    bridge = Bridge("TestCLI")

    def add(a, b):
        return a + b

    bridge.register(
        add,
        params={"a": InputParamSource(), "b": InputParamSource()},
        output=DisplayOutputDestination(),
    )
    cli = CLI(bridge)
    assert hasattr(cli, "run")
    assert hasattr(cli, "help_display")
    cli.help_display.print_help()
