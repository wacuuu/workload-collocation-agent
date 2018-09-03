"""
Module is responsible for creating and initialization related software components
using yaml based configuration file.

It is a simple dependency injection framework that only take cares of initialization
phase of life cycle of objects (not full IoC container).

It is connected with 'components' module which plays a role of registry of all components.

One additionally feature is builtin support for including other yaml files
using special tag called !file (check _file_loader_constructor docs for detailed descriptor).
"""
from typing import Any
import functools
import inspect
import io
import logging
import os
import typing
import warnings

from ruamel import yaml

from owca import logger

warnings.simplefilter('ignore', yaml.error.UnsafeLoaderWarning)


log = logging.getLogger(__name__)


ROOT_PATH = ''

_registered_tags = set()


class ConfigLoadError(Exception):
    """Error raised for any of improper config file. """
    pass


def _constructor(loader: yaml.loader.Loader, node: yaml.nodes.Node, cls: type):
    """Create instance of registered class ('cls" from closure) in recursive manner.
    First create "blank" uninitialized instance, then validate provided data,
    and then when whole hierarchy was processed initialize them in reverse order.
    Creation happens from top.
    Initialization happens from bottom.

    To split creation from initialization we relay on internal ruamel implementation
    that uses generators to allow lazy object initialization. If constructor is generator
    (contain 'yield' keyword) constructor will be called by next() at least twice (if deep=False)
    or many times until exhaustion (deep=True)).
    Our own constructor is just really thin wrapper over default "construct_mapping" and we
    use "generator lazy initialization" feature - to use created mapping
    as arguments for cls.__init__.
    """
    # Create "blank" uninitialized instance of cls.
    instance = object.__new__(cls)

    log.log(logger.TRACE, 'construct %s', cls.__name__)

    # Replace all scalar nodes to "simple" mappings without value
    # in order to allow create empty instances.
    # TODO: consider using first flat parameter as "args"
    if isinstance(node, yaml.ScalarNode):
        if node.value is not None and node.value != '':
            log.warning('Value %r for class %r ignored!' % (node.value, cls.__name__))
        arguments = {}
    else:
        # construct_mapping: deep is used to first create underlying objects, deep=True is
        # always used for mapping type.
        arguments = loader.construct_mapping(node, deep=True)

    # Constructor arguments simple type validation.
    # Use annotated constructor (arguments type annotations) to validate provided arguments.
    signature = inspect.signature(cls.__init__)
    for name, parameter in signature.parameters.items():
        if name == 'self':
            continue

        assert parameter.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ), 'YAML constructor only supports named ' \
            'keyword arguments got parameter %r(%r) for %r' % (parameter, parameter.kind, cls)

        expected_type = parameter.annotation

        # Ignore type check if there is no type annotation or for generic types because:
        # "Parameterized generics cannot be used with class or instance checks" limitation.
        if expected_type == inspect._empty or isinstance(expected_type, typing.GenericMeta):
            continue

        # Only validate provided values (ignore defaults).
        if name in arguments:
            value = arguments[name]
            if not isinstance(value, expected_type):
                raise ConfigLoadError(
                    'Value %r%s for field %r in class %r '
                    'has improper type (got=%r expected=%r)!' %
                    (value, node.start_mark, name, cls.__name__, type(value), expected_type))

    # End the creation step.
    yield instance

    # Continue with initialization.
    log.log(logger.TRACE, 'constructed object init %s(id=0x%x) with state=%r ',
            cls.__name__, id(instance), arguments)
    try:
        instance.__init__(**arguments)
    except TypeError as e:
        raise ConfigLoadError(
            'Cannot instantiate %r%s with arguments=%r (constructor signature is: %s)' % (
                cls.__name__, node.start_mark, arguments, signature))
    log.log(logger.TRACE, '%s(0x%x)=%r', cls.__name__, id(instance), vars(instance))


def register(cls):
    """Register constructor from yaml for a given class.
    The class can be then initialized during yaml processing if appropriate tag is found.

    E.g. if we have Foo class then you can use '!Foo' in yaml file.

        foo: !Foo
            x: 1

    after processing this file with "load_config", we get:

        {
            "foo": <Foo: instance...>
        }

    To initialize the class, constructor will simply call __init__, with
    already preprocessed body of deeper yaml nodes. In above example:

        foo = Foo.__new__(Foo)  # construct uninitialized (blank) instance of given class
        foo.__init__(x=1) # initialize instance

    """

    # Just simply register new constructor for given cls.
    log.log(logger.TRACE, 'registered class %r' % (cls.__name__))
    yaml.add_constructor('!%s' % cls.__name__, functools.partial(_constructor, cls=cls))
    _registered_tags.add(cls.__name__)
    return cls


def _parse(yaml_body: io.StringIO) -> Any:
    """Parses configuration from given yaml body and returns initialized object."""
    try:
        return yaml.load(yaml_body)
    except yaml.constructor.ConstructorError as e:
        raise ConfigLoadError(
            '%s %s. ' % (e.problem, e.problem_mark) +
            'Available tags are: %s' % (', '.join(_registered_tags))
        )


def load_config(filename: str) -> Any:
    """Reads config from base file (which can contain nested config file).

    :param filename: The base config file
    :returns deserialized objects from yaml
    """
    try:
        with open(filename) as f:
            return _parse(f)
    except FileNotFoundError as e:
        raise ConfigLoadError('Cannot find configuration file: %r' % filename)


def _file_loader_constructor(loader: yaml.loader.Loader, node: yaml.nodes.Node):
    """This function is called, when a yaml node
    is tagged as 'file'. It loads the yaml file
    passed as the tag argument and places it under
    the current node.

    Module for loading nested config files

    E.g.

    ------------------------
    File -> base.yaml

    key1: 'value1'
    key2: 1.2
    key3: !file nested1.yaml
    -------------------------

    File -> nested1.yaml

    nested_key1: 'nested_value'
    another_nested_key: true
    ------------------------

    Result

    key1: 'value1'
    key2: 1.2
    key3:
    nested_key1: 'nested_value'
    another_nested_key: true
    """
    filename = loader.construct_scalar(node)
    log.debug('loading from file: %s', filename)
    if filename == '':
        raise ConfigLoadError('For a !file node a filename must be provided!%s', node.start_mark)

    full_filename = os.path.join(os.path.dirname(loader.name), filename)

    with open(full_filename) as f:
        if not filename.endswith(('.yaml', '.yml')):
            raise ConfigLoadError('Unsupported file %r%stype (use: YAML)!' % (
                full_filename, node.start_mark))
        content = yaml.load(f)
    return content


yaml.add_constructor(u'!file', _file_loader_constructor)
