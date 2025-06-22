"""
tests.test_core_hooks
Test event hooks in bridges core.
"""

from bridges.core.basic import Bridge
from bridges.core.types import DisplayOutputDestination, InputParamSource


def test_event_hooks():
    events = {"pre": False, "post": False, "error": False}

    def pre(params, meta):
        events["pre"] = True

    def post(result, meta):
        events["post"] = True

    def error(exc, meta):
        events["error"] = True

    def fail(a):
        raise Exception("fail")

    def add(a: str, b: str):
        return int(a) + int(b)

    bridge = Bridge("TestHooks")
    bridge.add_pre_hook(pre)
    bridge.add_post_hook(post)
    bridge.add_error_hook(error)
    meta = bridge.register(
        add,
        params={"a": InputParamSource(), "b": InputParamSource()},
        output=DisplayOutputDestination(),
    )
    meta({"a": "1", "b": "2"})
    assert events["pre"] and events["post"]
    meta_fail = bridge.register(
        fail, params={"a": InputParamSource()}, output=DisplayOutputDestination()
    )
    try:
        meta_fail({"a": "1"})
    except Exception:
        pass
    assert events["error"]
