from bridges.core.basic import Bridge


def test_context_history_and_restore():
    bridge = Bridge("TestContext")
    bridge.update_context("a", 1)
    bridge.update_context("b", 2)
    assert bridge.context["a"] == 1
    assert bridge.context["b"] == 2
    history = bridge.get_context_history()
    assert isinstance(history, list)
    assert len(history) >= 3
    bridge.clear_context()
    assert bridge.context == {}
    bridge.update_context("x", 42)
    idx = len(bridge.context_history) - 2
    bridge.restore_context(idx)
    assert "x" not in bridge.context or bridge.context["x"] != 42
