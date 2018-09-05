import pytest
from unittest.mock import patch, Mock, call
from io import StringIO

from owca.metrics import Metric, MetricType
from owca.storage import FailedDeliveryException
from owca.wrapper.parser import (default_parse, kafka_store_with_retry,
                                 DEFAULT_REGEXP, MAX_ATTEMPTS, readline_with_check)


@pytest.mark.parametrize("input,separator,expected", [
    (StringIO("x=4 y=5 \n"
              "x=2 y=6"), None,
     [Metric("x", 4.0, type=MetricType.COUNTER), Metric("y", 5.0, type=MetricType.COUNTER)]),
    (StringIO("x=4 y=5 \n"
              "z=2 w=6 \n"
              "---"), "---",
     [Metric("x", 4.0, type=MetricType.COUNTER), Metric("y", 5.0, type=MetricType.COUNTER),
      Metric("z", 2.0, type=MetricType.COUNTER), Metric("w", 6.0, type=MetricType.COUNTER)]),
    (StringIO("Metrics: x=4.5 y=5.4 \n"
              "z=1.337,w=6.66 \n"
              "---"), "---",
     [Metric("x", 4.5, type=MetricType.COUNTER), Metric("y", 5.4, type=MetricType.COUNTER),
      Metric("z", 1.337, type=MetricType.COUNTER), Metric("w", 6.66, type=MetricType.COUNTER)]),
])
def test_default_parse(input, separator, expected):
    assert default_parse(input, DEFAULT_REGEXP, separator) == expected


def test_default_parse_no_source_no_separator():
    with pytest.raises(StopIteration):
        default_parse(input=StringIO(''), regexp=DEFAULT_REGEXP, separator=None)


def test_default_parse_no_source_separator():
    with pytest.raises(StopIteration):
        default_parse(input=StringIO("x=4 y=5 \n"
                                     "z=2 w=5\n"
                                     # last line is an empty string, which should raise the
                                     # exception
                                     ""), regexp=DEFAULT_REGEXP, separator="---")


def test_readline_with_check():
    with pytest.raises(StopIteration):
        readline_with_check(input=StringIO(""))
    line = "content_of_line"
    assert line == readline_with_check(input=StringIO(line))


@patch('time.sleep')
def test_kafka_store_with_retry_failure(sleep_mock):
    kafka_mock = Mock()
    kafka_mock.store = Mock(side_effect=[FailedDeliveryException] * MAX_ATTEMPTS)
    with pytest.raises(FailedDeliveryException):
        kafka_store_with_retry(kafka_mock, Mock())
    sleep_mock.assert_has_calls([call(1), call(2), call(4), call(8)])


@patch('time.sleep')
def test_kafka_store_with_retry_success(sleep_mock):
    kafka_mock = Mock()
    kafka_mock.store = Mock(
        side_effect=[FailedDeliveryException, FailedDeliveryException, Mock()])
    kafka_store_with_retry(kafka_mock, Mock())
    sleep_mock.assert_has_calls([call(1), call(2)])
    # No other assert can be made, test should not throw an exception
