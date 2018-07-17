from io import StringIO

from rmi import config

import pytest

foo_yaml = """
x: !FooNeverRegistered
"""

def test_config_unknown_tag():

    with pytest.raises(config.ConfigLoadError, match="could not determine a constructor for the tag '!FooNeverRegistered'.*Available tags are: "):
        config._parse(StringIO(foo_yaml))


bar_yaml = """
b: !Bar
    y: 5
"""

@config.register
class Bar:

    def __init__(self, x: int):
        pass

def test_config_incorrect_constructor():
    with pytest.raises(config.ConfigLoadError, match="Cannot instantiate 'Bar'"):
        config._parse(StringIO(bar_yaml))
