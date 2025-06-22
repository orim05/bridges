"""
tests.test_basic
Basic functionality tests.
"""

def test_basic_import():
    """Test that basic imports work."""
    from bridges.core.basic import Bridge
    from bridges.interfaces.cli import CLI
    
    bridge = Bridge("Test")
    cli = CLI(bridge)
    assert hasattr(cli, 'run')
