import pytest

from owca.logger import configure_loggers_from_dict, parse_loggers_from_list

from unittest.mock import patch


@pytest.mark.parametrize('log_levels_list,expected_log_levels_dict', (
    ([], {}),
    (['DEBUG'], {'owca': 'DEBUG'}),
    (['DEBUG', 'foo.bar:info'], {'owca': 'DEBUG', 'foo.bar': 'info'}),
))
def test_parsing_cmdline(log_levels_list, expected_log_levels_dict):
    log_levels_dict = parse_loggers_from_list(log_levels_list)
    assert log_levels_dict == expected_log_levels_dict


@patch('owca.logger.init_logging')
def test_configuring_loggers(init_logging_mock):
    configure_loggers_from_dict({'foo': 'debug'})
    init_logging_mock.assert_called_once_with('debug', package_name='foo')
