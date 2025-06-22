from bridges.core.basic import Bridge
from bridges.core.types import ParamSource, OutputDestination
from bridges.interfaces.cli import CLI


class MyParam(ParamSource):
    def get_value(self, context):
        return 99


class MyOutput(OutputDestination):
    def send(self, value, context):
        if hasattr(context, "update_context"):
            context.update_context("sent", value)
        else:
            context["sent"] = value


def test_cli_with_custom_param_output():
    bridge = Bridge("TestCustomCLI")

    def f(a: int):
        return a * 2

    bridge.register(f, params={"a": MyParam()}, output=MyOutput())
    cli = CLI(bridge)
    # Simulate call
    meta = bridge.functions["f"]
    result = meta({"a": 3})
    assert result == 6
    context = {}
    meta.output[0].send(result, context)
    assert context["sent"] == 6
