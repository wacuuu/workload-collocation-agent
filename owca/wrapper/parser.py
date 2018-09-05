import _thread
import logging
import re
import time
from io import TextIOWrapper
from typing import List, Dict, Callable

import owca
from owca.metrics import Metric, MetricType
from owca.storage import KafkaStorage

log = logging.getLogger(__name__)
ParseFunc = Callable[[TextIOWrapper, str, str, Dict[str, str]], List[Metric]]

# Matches values returned in format "a=4.2". If different format is needed,
# provide regex in arguments. It needs to have 2 named groups "name" and "value"
DEFAULT_REGEXP = "(?P<name>\w+?)=(?P<value>\d+?.?\d*)"

MAX_ATTEMPTS = 5


def readline_with_check(input: TextIOWrapper) -> str:
    """Additionally check if EOF."""
    EOF_line = ""
    new_line = input.readline()
    if new_line == EOF_line:
        raise StopIteration
    return new_line


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

    new_line = readline_with_check(input)
    if separator is not None:
        # With separator, first we read the whole block of output until the separator appears
        while new_line != separator and not new_line == '':
            input_lines.append(new_line)
            new_line = readline_with_check(input)
        log.debug("Found separator in {0}".format(new_line))
    else:
        # Without separator only one line is processed at a time
        input_lines.append(new_line)
    found_metrics = re.finditer(regexp, '\n'.join(input_lines))
    for metric in list(found_metrics):
        metric = metric.groupdict()
        new_metrics.append(Metric(metric['name'], float(metric['value']),
                                  type=MetricType.COUNTER, labels=labels))
        log.debug("Found metric name: {0}, value: {1}".format(metric["name"], metric["value"]))
    return new_metrics


def kafka_store_with_retry(kafka_storage: KafkaStorage, metrics: List[Metric]):
    # Try MAX_ATTEMPTS times to send metrics to kafka server
    # with increasing sleep time between attempts
    backoff_delay = 1
    for attempt in range(MAX_ATTEMPTS):
        try:
            kafka_storage.store(metrics)
        except owca.storage.FailedDeliveryException:
            log.warning("Failed to deliver message to kafka, "
                        "tried {0} times".format(attempt + 1))
            if attempt == MAX_ATTEMPTS - 1:
                raise
            time.sleep(backoff_delay)
            backoff_delay *= 2
            continue
        break


def parse_loop(parse: ParseFunc, kafka_storage: KafkaStorage):
    """
    Runs parsing and kafka storage in loop. parse_loop.last_valid_metrics list is accessed
    by the HTTP server GET request handler.
    """
    parse_loop.metrics = []
    parse_loop.last_valid_metrics = []
    while True:
        try:
            parse_loop.metrics = parse()
            # parse() can return an empty list, so we store new values for kafka and http server
            # only when there are new metrics to store
            if parse_loop.metrics:
                parse_loop.last_valid_metrics = parse_loop.metrics.copy()
                kafka_store_with_retry(kafka_storage, parse_loop.last_valid_metrics)

        except BaseException:
            _thread.interrupt_main()
            raise
