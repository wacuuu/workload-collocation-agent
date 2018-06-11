#!/bin/env python3
import argparse
import subprocess
import threading
import re
import math
import prometheus_client
import logging
import sys
import signal

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


class Accumulator():
    """
    Class allows to share Application Performance Metrics between collecting thread and exposing thread.
    """

    def __init__(self, baseline: int):
        """
        :param baseline: reference performance of single-threaded application
        """
        self.counters = []
        self.baseline = baseline

    def add_counter(self, value: int):
        """
        Adds value to list of collected counter values
        :param value: collected value of a counter
        :return:
        """
        logger.debug("Appeding value %d", value)
        self.counters.append(value)

    def get_sum_of_counters(self):
        """
        Sums collected counters, clear the list and returns sum normalized against baseline.
        :return:
        """
        sum = math.fsum(self.counters)
        normalized_sum = sum / self.baseline
        logger.debug(
            "Returning sum of counters. Raw: %d, normalized: %f",
            sum,
            normalized_sum)
        self.counters = []
        return normalized_sum


class Parser:
    """
    Class allows to parse stress-ng output and saves counter values for future reference.
    """

    def __init__(self, stress: subprocess.Popen, accumulator: Accumulator):
        """
        :param stress: stress-ng process handler
        :param accumulator: class that allow to share information between Parser and Prometheus thread
        """
        self._stress = stress
        self._accumulator = accumulator
        self._stderr_lines = []

    def parse_line(self):
        """
        Extracts counter values from stress-ng output row (stress-ng: info:  [22954] Time 1528374162, counter: 34)
        and stores it in accumulator.
        """
        for line in self._stress.stderr:
            self._stderr_lines.append(line)
            logger.debug('Parsing line: %s', line)
            counter = re.search('counter: (\d+)', line)
            if counter is not None:
                value = int(counter.group(1))
                logger.debug("Counter value found: %d", value)
                self._accumulator.add_counter(value)

    def get_stderr(self):
        """
        Retrives a list of parsed stderr lines, resets internal state and returns the list.
        :return:
        """
        stderr = self._stderr_lines
        self._stderr_lines = []
        return stderr


def main():
    parser = _prepare_argument_parser()
    # It is assumed that unknown arguments should be passed to stress-ng.
    args, stress_args = parser.parse_known_args()

    # Configuring a logger.
    logger.setLevel(args.log_level)
    logger.debug("Logger configured with %s level", args.log_level)

    stress = _launch_stress_ng(stress_args)

    accumulator = Accumulator(args.baseline)
    parser = Parser(stress, accumulator)
    processor = _launch_output_parser(parser)

    # Let's be nice and tidy - handle signals not aviod noisy output
    def stop_handler(signum, _):
        stress.terminate()
        logger.info('stress-ng terminated with signal %d', signum)
    signal.signal(signal.SIGABRT, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    _launch_prometheus(accumulator, args.prometheus_port)
    # Processor thread will stop when there are no more lines of output to parse.
    processor.join()
    stress.wait()
    if stress.returncode is not 0:
        _exit_on_error(stress, parser.get_stderr())
    _exit_on_success(stress, parser.get_stderr())


def _exit_on_success(stress: subprocess.Popen, stderr):
    logger.info("stress-ng exited normally")
    logger.debug(
        'stress-ng stderr: %s%s',
        ' '.join(stderr),
        stress.stderr.read())
    logger.debug('stress-ng stdout: %s', stress.stdout.read())


def _prepare_argument_parser():
    parser = argparse.ArgumentParser(
        description='stress-ng wrapper that exposes APMs over HTTP using Prometheus format.')
    parser.add_argument(
        '--baseline',
        help='Baseline performance of single thread that will be used to normalize observed value',
        dest='baseline',
        default=1,
        type=int)
    parser.add_argument(
        '--prometheus_port',
        help='Port to be used to expose the metrics',
        dest='prometheus_port',
        default=9000,
        type=int)
    parser.add_argument(
        '--log_level',
        help='Logging level',
        dest='log_level',
        default='ERROR',
        choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'],
        type=str)
    return parser


def _launch_output_parser(parser: Parser):
    logger.debug("Starting output parsing thread.")
    processor = threading.Thread(target=parser.parse_line)
    processor.start()
    return processor


def _exit_on_error(stress: subprocess.Popen, stderr):
    logger.error(
        'stress-ng terminated with return code %d',
        stress.returncode)
    logger.debug(
        'stress-ng stderr: %s%s',
        ' '.join(stderr),
        stress.stderr.read())
    logger.debug('stress-ng stdout: %s', stress.stdout.read())
    sys.exit(stress.returncode)


def _launch_prometheus(accumulator: Accumulator, port: int):
    logger.debug("Configuring gauge and launching Prometheus HTTP server.")
    iterations = prometheus_client.Gauge(
        'number_of_iterations',
        'Number of iterations if internal stress-ng loop per period of time.')
    iterations.set_function(accumulator.get_sum_of_counters)
    prometheus_client.start_http_server(port)


def _launch_stress_ng(stress_args):
    stress_args.insert(0, 'stress-ng')
    stress = subprocess.Popen(
        stress_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1024)
    logger.info('stress-ng launched')
    logger.debug('stress-ng arguments: %s', ' '.join(stress_args))
    return stress


if __name__ == "__main__":
    main()
