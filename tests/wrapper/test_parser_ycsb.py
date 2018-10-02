from io import StringIO

from owca.metrics import Metric, MetricType
from owca.wrapper.parser_ycsb import parse


def test_parse():
    input_ = StringIO(
        "2018-08-22 17:33:25:811 581 sec: 581117 operations; "
        "975 current ops/sec; "
        "est completion in 2 hours 36 minutes "
        "[READ: Count=462, Max=554, Min=273, Avg=393.39, 90=457, "
        "99=525, 99.9=554, 99.99=554] [UPDATE: Count=513, Max=699, "
        "Min=254, Avg=383.83, 90=441, 99=512, 99.9=589, 99.99=699] # noq"
    )
    expected = [
        Metric("cassandra_operations", value=581117, type=MetricType.GAUGE,
               help="Done operations in Cassandra"),
        Metric("cassandra_ops_per_sec", value=975, type=MetricType.GAUGE,
               help="Ops per sec Cassandra"),
        Metric("cassandra_read_p9999", value=554.0, type=MetricType.GAUGE,
               help="99.99th percentile of read latency in Cassandra"),
        Metric("cassandra_update_p9999", value=699.0, type=MetricType.GAUGE,
               help="99.99th percentile of update latency in Cassandra"),
    ]
    assert expected == parse(input_, {})
