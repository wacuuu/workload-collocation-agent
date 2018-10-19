from io import TextIOWrapper

from typing import List, Dict
import re

from owca.metrics import Metric, MetricType
from owca.wrapper import wrapper_main

EOF_line = "Stop-Cassandra-Stress-Now"


def parse(input: TextIOWrapper, regexp: str, separator: str = None,
          labels: Dict[str, str] = {}, metric_name_prefix: str = '') -> List[Metric]:
    """Custom parse function for cassandra-stress.
        Results:
        Op rate                   :   14,997 op/s  [WRITE: 14,997 op/s]
        Partition rate            :   14,997 pk/s  [WRITE: 14,997 pk/s]
        Row rate                  :   14,997 row/s [WRITE: 14,997 row/s]
        Latency mean              :    1.9 ms [WRITE: 1.9 ms]
        Latency median            :    0.3 ms [WRITE: 0.3 ms]
        Latency 95th percentile   :    0.4 ms [WRITE: 0.4 ms]
        Latency 99th percentile   :   74.0 ms [WRITE: 74.0 ms]
        Latency 99.9th percentile :  146.8 ms [WRITE: 146.8 ms]
        Latency max               :  160.2 ms [WRITE: 160.2 ms]
        Total partitions          :  1,350,028 [WRITE: 1,350,028]
        Total errors              :          0 [WRITE: 0]
        Total GC count            : 0
        Total GC memory           : 0.000 KiB
        Total GC time             :    0.0 seconds
        Avg GC time               :    NaN ms
        StdDev GC time            :    0.0 ms
        Total operation time      : 00:01:30
    """

    new_metrics = []
    new_line = input.readline()

    if "Op rate" in new_line:
        read_op_rate = re.search(r'Op rate[ ]*:[ ]*([0-9,]*) op/s', new_line)
        op_rate = float(''.join(read_op_rate.group(1).split(',')))
        new_metrics.append(Metric('cassandra_stress_op_rate', op_rate,
                                  type=MetricType.GAUGE, labels=labels,
                                  help="Cassandra Op Rate"))

    if "Latency 99th percentile" in new_line:
        read = re.search(
            r'Latency 99th percentile[ ]*:[ ]*([0-9]*\.[0-9]*) ms', new_line)
        p99 = float(read.group(1))
        new_metrics.append(Metric('cassandra_stress_p99', p99,
                                  type=MetricType.GAUGE, labels=labels,
                                  help="99th percentile of latency in Cassandra"))

    if EOF_line in new_line:
        raise StopIteration

    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(parse)
