from io import StringIO

from owca.metrics import Metric, MetricType
from owca.wrapper.parser_tensorflow_benchmark_prediction import parse


def test_parse():
    input_ = StringIO(
        "580	248.7 examples/sec"
    )
    expected = [
        Metric('tensorflow_prediction_speed', value=248.7, type=MetricType.GAUGE,
               help="Tensorflow Prediction Speed")
    ]
    assert expected == parse(input_, None, None, {}, 'tensorflow_benchmark_prediction_')
