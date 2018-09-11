from io import TextIOWrapper
import logging
from typing import List, Dict
import re

from owca.metrics import Metric, MetricType
from owca.wrapper import wrapper_main
from owca.wrapper.parser import readline_with_check

log = logging.getLogger(__name__)
EMPTY_LINE = r"^\s*$"


def parse(input: TextIOWrapper, labels: Dict[str, str] = {},
          *args, **kwargs) -> List[Metric]:
    """
    Custom parse function for specjbb.
    For sample output from specjbb see file:
    ./specjbb_sample_stdout.txt

    Discards until finds
    >>Response times:<<
    and read until empty line.

    Readed lines represents a table.
    In the code the table representation is named data_frame.
    """
    new_metrics = []
    input_lines = []

    # discarding lines
    new_line = readline_with_check(input)
    while not re.match("^\s*Response times:\s*$", new_line):
        new_line = readline_with_check(input)
    new_line = readline_with_check(input)

    # reading until empty line
    while not re.match(EMPTY_LINE, new_line):
        input_lines.append(new_line)
        new_line = readline_with_check(input)
    log.debug("Found separator in {0}".format(new_line))

    # Two dimensional list, first row contains names of columns. Almost as data frame.
    data_frame = [[el.strip() for el in line.split(",")] for line in input_lines]

    # For now we need only one metric: TotalPurchase, p99.
    metric_name = "specjbb_p99_total_purchase"
    metric_value = float(data_frame[1][-3])  # total purchase, p99
    new_metrics.append(Metric(metric_name, metric_value,
                              type=MetricType.GAUGE, labels=labels,
                              help="Specjbb2015 metric, Total Purchase, percentile 99"))

    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(parse)
