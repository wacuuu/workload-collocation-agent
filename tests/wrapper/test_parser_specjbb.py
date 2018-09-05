import os

from owca.metrics import Metric, MetricType
from owca.wrapper.parser_specjbb import parse


def test_parse():
    """Reads textfile with sample output from specjbb."""
    expected = [Metric("specjbb_p99_total_purchase", value=0,
                       type=MetricType.GAUGE,
                       help="Specjbb2015 metric, Total Purchase, percentile 99")]

    path = os.path.dirname(os.path.abspath(__file__))
    with open(path + '/specjbb_sample_stdout.txt', 'r') as fin:
        expected[0].value = 3800000.0
        assert expected == parse(fin, {})
        expected[0].value = 581000.0
        assert expected == parse(fin, {})
        expected[0].value = 6800000.0
        assert expected == parse(fin, {})
