from io import StringIO

from owca.metrics import Metric, MetricType
from owca.wrapper.parser_mutilate import parse


def test_parse():
    input_ = StringIO(
        "#type       avg     std     min     5th    10th    90th    95th    99th"
        "read      801.9   155.0   304.5   643.7   661.1  1017.8  1128.2  1386.5"
        "update    804.6   157.8   539.4   643.4   661.2  1026.1  1136.1  1404.3"
        "op_q        1.0     0.0     1.0     1.0     1.0     1.1     1.1     1.1"

        "Total QPS = 159578.5 (1595835 / 10.0s)"

        "Misses = 0 (0.0%)"
        "Skipped TXs = 0 (0.0%)"

        "RX  382849511 bytes :   36.5 MB/s"
        "TX   67524708 bytes :    6.4 MB/s"
    )
    expected = [
        Metric('memcached_read_p95', value=1128.2, type=MetricType.GAUGE,
               help="95th percentile of read latency in Memcached"),
        Metric('memcached_qps', value=159578.5, type=MetricType.GAUGE,
               help="QPS in Memcached")
    ]
    assert expected == parse(input_, None, None, {}, 'mutilate_')
