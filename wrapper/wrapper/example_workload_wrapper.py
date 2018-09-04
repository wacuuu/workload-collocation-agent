from io import TextIOWrapper
from typing import List, Dict

from owca.metrics import Metric, MetricType
from wrapper import wrapper_main


def example_parse_function(input: TextIOWrapper, regexp: str, separator: str = None,
                           labels: Dict[str, str] = {}) -> List[Metric]:
    return [Metric(name="example", value=1.337, labels={"test": "label"}, type=MetricType.GAUGE,
                   help="Empty example metric")]


if __name__ == "__main__":
    wrapper_main.main(example_parse_function)
