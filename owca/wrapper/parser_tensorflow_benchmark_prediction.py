from io import TextIOWrapper
import logging
from typing import List, Dict
import re
from owca.metrics import Metric, MetricType
from owca.wrapper import wrapper_main
from owca.wrapper.parser import readline_with_check

log = logging.getLogger(__name__)


def parse(input: TextIOWrapper, regexp: str, separator: str = None,
          labels: Dict[str, str] = {}, metric_name_prefix: str = '') -> List[Metric]:
    """Custom parse function for tensorflow benchmark predition
        580    248.7 examples/sec
    """

    new_metrics = []
    log.debug(input)
    new_line = readline_with_check(input)

    if "examples/sec" in new_line:
        read = re.search(r'[0-9]*\t([0-9]*\.[0-9]*)[ ]*examples\/sec', new_line)
        p99 = float(read.group(1))
        new_metrics.append(Metric('tensorflow_prediction_speed', p99,
                                  type=MetricType.GAUGE, labels=labels,
                                  help="Tensorflow Prediction Speed"))

    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(parse)
