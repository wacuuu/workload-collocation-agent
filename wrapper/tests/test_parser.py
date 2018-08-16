import pytest
from io import StringIO

from rmi.metrics import Metric, MetricType
from wrapper.parser import default_parse, DEFAULT_REGEXP


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
