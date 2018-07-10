from rmi import config
from rmi import util


class OldClass:
    def __init__(self, x, y=3):
        self.x = x
        self.y = y


@config.register
class NewClass(OldClass):
    pass


@config.register
class Foo:
    def __init__(self, s: str, f: float = 1.) -> None:
        self.s = s
        self.f = f


@config.register
class Boo:
    def __init__(self, foo: Foo=None, items=None, nc: NewClass=None) -> None:
        self.foo = foo
        self.items = items
        self.nc = nc


class Item:
    def __init__(self, name):
        self.name = name


def test_config_with_simple_classes():

    # Another method for registering items (other than using decorator).
    config.register(Item)

    test_config_path = util.relative_module_path(__file__, 'test_config.yaml')

    data = config.load_config(test_config_path)

    foo_with_defaults = data['foo_with_defaults']
    assert foo_with_defaults.f == 1

    empty_boo = data['empty_boo']
    assert empty_boo.foo is None

    foo = data['foo']
    boo = data['boo']

    assert foo.s == 'some_string'
    assert foo.f == 2.5

    assert boo.foo is foo
    assert len(boo.items) == 2
    assert isinstance(boo.items[0], Item)
