from io import StringIO

from owca.metrics import Metric, MetricType
from owca.wrapper.parser_tensorflow_benchmark_training import parse


def test_parse():
    input_ = StringIO(
        "180	images/sec: 74.9 +/- 0.5 (jitter = 8.9)    2.409"
    )
    expected = [
        Metric('tensorflow_training_speed', value=74.9, type=MetricType.GAUGE,
               help="Tensorflow Training Speed")
    ]
    assert expected == parse(input_, None, None, {}, 'tensorflow_benchmark_training_')
