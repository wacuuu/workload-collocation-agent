import os

import pytest

from rmi import config
from rmi import testing
from rmi.config import ConfigLoadError

ROOT_PATH = testing.relative_module_path(__file__, 'resources')


def test_is_exception_raised_for_missing_filenameimport():
    with pytest.raises(ConfigLoadError):
        config.load_config(
            'missing_filename.yaml',
        )


def test_is_simple_file_loaded_correctly_with_root_path():
    cfg = config.load_config(os.path.join(ROOT_PATH, 'simple.yaml'))
    assert cfg['my_key'] == 'my_value'


def test_is_nested_file_imported_correctly_with_root_path():
    expected_cfg = {
        'key1': 'value1',
        'key2': 1.2,
        'key3': {
            'nested_key': 'nested_value',
            'x': 1
        }
    }

    actual_cfg = config.load_config(os.path.join(ROOT_PATH, 'base.yaml'))

    assert expected_cfg == actual_cfg


def test_is_double_nested_file_imported_correctly_with_root_path():
    expected_cfg = {
        'xyz': True,
        'second_key': 'qwerty',
        'nested_doc': {
            'key1': 'value1',
            'key2': 1.2,
            'key3': {
                'nested_key': 'nested_value',
                'x': 1
            }
        }
    }

    actual_cfg = config.load_config(os.path.join(ROOT_PATH, 'double_base.yaml'))
    assert expected_cfg == actual_cfg
