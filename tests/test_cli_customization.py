from bridges.core.basic import Bridge
from bridges.core.types import InputParamSource, DisplayOutputDestination
from bridges.interfaces.cli import CLI


def test_cli_custom_name_and_description():
    bridge = Bridge("TestCLI")

    def add(a, b):
        return int(a) + int(b)

    bridge.register(
        add,
        params={"a": InputParamSource(), "b": InputParamSource()},
        output=DisplayOutputDestination(),
    )
    cli = CLI(bridge, name="CustomCLI", description="Custom CLI Desc")
    assert cli.name == "CustomCLI"
    assert cli.description == "Custom CLI Desc"
    cli.customize({"banner_name": "AnotherName", "banner_description": "AnotherDesc"})
    assert cli.name == "AnotherName"
    assert cli.description == "AnotherDesc"
