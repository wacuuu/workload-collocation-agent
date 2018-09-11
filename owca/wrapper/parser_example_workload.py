from io import TextIOWrapper
from typing import List, Dict

from owca.metrics import Metric, MetricType
from owca.wrapper import wrapper_main


def parse(input: TextIOWrapper, regexp: str, separator: str = None,
          labels: Dict[str, str] = {}, metric_name_prefix: str = '') -> List[Metric]:
    return [Metric(name="example", value=1.337, labels={"test": "label"}, type=MetricType.GAUGE,
                   help="Empty example metric")]


if __name__ == "__main__":
    wrapper_main.main(parse)
