import logging
import re
from io import TextIOWrapper
from typing import List, Dict, Callable

from rmi.metrics import Metric, MetricType
from rmi.storage import KafkaStorage

log = logging.getLogger(__name__)
ParseFunc = Callable[[TextIOWrapper, str, str, Dict[str, str]], List[Metric]]

# Matches values returned in format "a=4.2". If different format is needed,
# provide regex in arguments. It needs to have 2 named groups "name" and "value"
DEFAULT_REGEXP = "(?P<name>\w+?)=(?P<value>\d+?.?\d*)"


def default_parse(input: TextIOWrapper, regexp: str, separator: str = None,
                  labels: Dict[str, str] = {}) -> List[Metric]:
    """
    Parses workload output. If no separator is provided, parses only one line at a time.
    With separator, it appends lines to a list until the line with separator appears and then
    uses regexp on the collected output. Separator should be sent in a separate line,
    without metrics. If there is no new lines in input from the workload, function stay at
    input.readline() call. After new data arrives, previously read values will be overwritten.
    :param input: output of the workload process
    :param regexp: regexp used for finding metric names and their values.
           Needs to contain 2 named groups "name" and "value".
    :param separator: string that separates blocks of measurements. If none is passed,
           only one line of input will be parsed
    :param labels: dictionary of labels like workload name, workload parameters etc.
           Used for labeling the metrics in prometheus format.
    :return: List of Metrics
    """
    new_metrics = []
    input_lines = []
    if separator is None:
        input_lines.append(input.readline())
    else:
        new_line = input.readline()
        while new_line != separator:
            input_lines.append(new_line)
            new_line = input.readline()
        log.debug("Found separator in {0}".format(new_line))

    found_metrics = re.finditer(regexp, '\n'.join(input_lines))
    for metric in list(found_metrics):
        metric = metric.groupdict()
        new_metrics.append(Metric(metric['name'], float(metric['value']),
                                  type=MetricType.COUNTER, labels=labels))
        log.debug("Found metric name: {0}, value: {1}".format(metric["name"], metric["value"]))
    return new_metrics


def parse_loop(parse: ParseFunc, kafka_storage: KafkaStorage):
    """
    Runs parsing and kafka storage in loop. parse_loop.metrics list is accessed by the HTTP server
    GET request handler.
    """
    parse_loop.metrics = []
    parse_loop.last_valid_metrics = []
    while True:
        parse_loop.metrics = parse()
        # parse() can return an empty list, so we store new values for kafka and http server
        # only when there are new metrics to store
        if parse_loop.metrics:
            kafka_storage.store(parse_loop.metrics)
            parse_loop.last_valid_metrics = parse_loop.metrics.copy()
