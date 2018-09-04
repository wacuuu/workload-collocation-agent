from io import TextIOWrapper
import logging
from typing import List, Dict
import re

from owca.metrics import Metric, MetricType
from owca.wrapper import wrapper_main

log = logging.getLogger(__name__)
EMPTY_LINE = "^\s*$"


def log_line(line, discarded=True):
    """
    :param discarded: if line was discarded by parse function
    """
    line = line.strip()
    if discarded:
        log.debug("- {0}".format(line))
    else:
        log.debug("+ {0}".format(line))


def specjbb_parse_function(input: TextIOWrapper, regexp: str, separator: str = None,
                           labels: Dict[str, str] = {}) -> List[Metric]:
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
    new_line = input.readline()
    while not re.match("^\s*Response times:\s*$", new_line):
        new_line = input.readline()
        log_line(new_line, True)
    new_line = input.readline()

    # reading until empty line
    while not re.match(EMPTY_LINE, new_line):
        input_lines.append(new_line)
        new_line = input.readline()
        log_line(new_line, False)
    log.debug("Found separator in {0}".format(new_line))

    # Two dimensional list, first row contains names of columns. Almost as data frame.
    data_frame = [[el.strip() for el in line.split(",")] for line in input_lines]

    # For now we need only one metric: TotalPurchase, p99.
    metric_name = "specjbb_p99_total_purchase"
    metric_value = float(data_frame[1][-3])  # total purchase, p99
    new_metrics.append(Metric(metric_name, metric_value,
                              type=MetricType.GAUGE, labels=labels,
                              help="Specjbb2015 metric, Total Purchase, percentile 99"))
    log.debug("Found metric name: {0}, value: {1}".format(metric_name, metric_value))

    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(specjbb_parse_function)
