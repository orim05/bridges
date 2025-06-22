"""
tests.test_custom_types
Test custom parameter sources and output destinations.
"""

from bridges.core.basic import Bridge
from bridges.core.types import OutputDestination, ParamSource


def test_custom_param_output():
    class MyParam(ParamSource):
        def get_value(self, context):
            return 42

    class MyOutput(OutputDestination):
        def send(self, value, context):
            if hasattr(context, "update_context"):
                context.update_context("sent", value)
            else:
                context["sent"] = value

    bridge = Bridge("TestCustom")

    def f(a: int):
        return a * 2

    meta = bridge.register(f, params={"a": MyParam()}, output=MyOutput())
    context = {}
    result = meta({"a": 3})
    assert result == 6
    # Simulate output
    meta.output[0].send(result, context)
    assert context["sent"] == 6
