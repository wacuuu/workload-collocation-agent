from io import TextIOWrapper
import logging
from typing import List, Dict
import re

from owca.metrics import Metric, MetricType
from owca.wrapper import wrapper_main
from owca.wrapper.parser import readline_with_check

log = logging.getLogger(__name__)


def parse(input: TextIOWrapper, regexp: str, separator: str = None,
          labels: Dict[str, str] = {}) -> List[Metric]:
    """Custom parse function for YCSB.
    Parses lines similar to (added new line characters to improve readibility):
        2018-08-22 17:33:25:811 581 sec: 581117 operations;
        975 current ops/sec;
        est completion in 2 hours 36 minutes
        [READ: Count=462, Max=554, Min=273, Avg=393.39, 90=457,
        99=525, 99.9=554, 99.99=554] [UPDATE: Count=513, Max=699,
        Min=254, Avg=383.83, 90=441, 99=512, 99.9=589, 99.99=699] # noqa
    """
    new_metrics = []

    new_line = readline_with_check(input)
    if "READ" in new_line:
        read = re.search('\[READ.*?99\.99=(\d+).*?\]', new_line)
        p9999 = float(read.group(1))
        log.debug("99.99th READ percentile found: {}".format(p9999))
        new_metrics.append(Metric('cassandra_read_p9999', p9999,
                                  type=MetricType.GAUGE, labels=labels,
                                  help="99.99th percentile of read latency in Cassandra"))
    if "UPDATE" in new_line:
        update = re.search('\[UPDATE.*?99\.99=(\d+).*?\]', new_line)
        p9999 = float(update.group(1))
        log.debug("99.99th UPDATE percentile found: {}".format(p9999))
        new_metrics.append(Metric('cassandra_update_p9999', p9999,
                                  type=MetricType.GAUGE, labels=labels,
                                  help="99.99th percentile of update latency in Cassandra"))

    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(parse)
