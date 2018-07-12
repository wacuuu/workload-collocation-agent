"""
Module is responsible for creating and initialization related software components
using yaml based configuration file.

It is a simple dependency injection framework that only take cares of initialization
phase of life cycle of objects (not full IoC container).

It is connected with 'components' module which plays a role of registry of all components.

One additionally feature is builtin support for including other yaml files
using special tag called !file (check _file_loader_constructor docs for detailed descriptor).
"""
import inspect
import json
import logging
import os
import typing
import functools
import warnings

from ruamel import yaml

from rmi import logger

warnings.simplefilter('ignore', yaml.error.UnsafeLoaderWarning)


log = logging.getLogger(__name__)


ROOT_PATH = ''


class ValidationError(Exception):
    pass


def _constructor(loader: yaml.loader.Loader, node: yaml.nodes.Node, cls: type):
    """Create instance of registered class ('cls" from closure) in recursive manner.
    First create "blank" uninitialized instance, then validate provided data,
    and then when whole hierarchy was processed initialize them in reverse order.
    Creation happens from top.
    Initialization happens from bottom.
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
        state = {}
    else:
        state = loader.construct_mapping(node, deep=True)
    # End the creation step.
    yield instance

    # Use annotated constructor to verify parameters simple types.
    signature = inspect.signature(cls.__init__)
    for name, parameter in signature.parameters.items():
        if name == 'self':
            continue

        assert parameter.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ), 'YAML constructor only support named ' \
            'keyword arguments got parameter %r for %r' % (parameter, cls)

        expected_type = parameter.annotation

        # Ignore type check for generic types because or there is no annotation:
        # "Parameterized generics cannot be used with class or instance checks" limitation.
        if expected_type == inspect._empty or isinstance(expected_type, typing.GenericMeta):
            continue

        # Only validate provided values (ignore defaults).
        if name in state:
            value = state[name]
            if not isinstance(value, expected_type):
                raise ValidationError(
                    'Value %r for field %r in class %r '
                    'has improper type (got=%r expected=%r)!' %
                    (value, name, cls.__name__, type(value), expected_type))

    # Continue with initialization.
    log.log(logger.TRACE, 'init %s(id=0x%x) with state=%r ', cls.__name__, id(instance), state)
    try:
        instance.__init__(**state)
    except TypeError as e:
        raise TypeError('Cannot instantiate %r with kw=%r (constructor signature is: %s)' % (
            cls.__name__, state, signature)) from e
    log.log(logger.TRACE, '%s(0x%x)=%r', cls.__name__, id(instance), vars(instance))


def register(cls):
    """Register constructor from yaml for a given class.
    The class can be then initialized during yaml processing if appropriate tags is found.

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
    return cls


def load_config(filename):
    """
    Reads config from base file
    (which can contain nested config file)

    :param filename: The base config file
    :param root_path: Root path for all referenced files
    :returns a dict containing the actual configuration
    """
    with open(filename) as f:
        return yaml.load(f)


def _file_loader_constructor(loader, node):
    """
    This function is called, when a yaml node
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
        raise RuntimeError('For a !file node a filename must be provided!')

    full_filename = os.path.join(os.path.dirname(loader.name), filename)

    with open(full_filename) as f:
        if filename.endswith('.json'):
            content = json.load(f)
        elif filename.endswith(('.yaml', '.yml')):
            content = yaml.load(f)
        else:
            raise RuntimeError('Unsupported file %r type (use: JSON or YAML)!' % full_filename)

    return content


yaml.add_constructor(u'!file', _file_loader_constructor)
