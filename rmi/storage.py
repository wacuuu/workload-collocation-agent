"""
Module is responsible for exposing functionality of storing labeled metrics
in durable external storage.
"""
import abc
import time
import logging
from typing import List
import re

import confluent_kafka
from dataclasses import dataclass, field

from rmi import logger
from rmi.metrics import Metric, MetricType

log = logging.getLogger(__name__)


class Storage(abc.ABC):

    @abc.abstractmethod
    def store(self, metrics: List[Metric]) -> None:
        """store metrics; may throw FailedDeliveryException"""
        ...


class LogStorage(Storage):

    def store(self, metrics):
        log.debug(metrics)


class FailedDeliveryException(Exception):
    """when metrics has not been stored with success"""
    pass


def get_current_time() -> str:
    """current time in unix epoch (miliseconds)"""
    return str(int(time.time()) * 1000)


_METRIC_NAME_RE = re.compile(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$')
_METRIC_LABEL_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
_RESERVED_METRIC_LABEL_NAME_RE = re.compile(r'^__.*$')


class UnconvertableToPrometheusExpositionFormat(Exception):
    pass


def is_convertable_to_prometheus_exposition_format(metrics: List[Metric]) -> (bool, str):
    """Check if metrics are convertable into prometheus exposition format.

    In case of metric type we modify scope of original prometheus exposition format requirements
    and only allow to set type to gauge and counter.

    Returns:
        Tuple with 1) boolean flag whether the metrics are convertable (True if they are)
        2) in case of not being convertable error message explaining the cause, otherwise
        empty string.
    """
    for metric in metrics:
        if not _METRIC_NAME_RE.match(metric.name):
            return (False, "Wrong metric name {}.".format(metric.name))
        for label_key, label_val in metric.labels.items():
            if not _METRIC_LABEL_NAME_RE.match(label_key):
                return (False, "Used wrong label name {} in metric {}."
                               .format(label_key, metric.name))
            if _RESERVED_METRIC_LABEL_NAME_RE.match(label_key):
                return (False, "Used reserved label name {} in metric {}."
                               .format(label_key, metric.name))

        # Its our internal RMI requirement to use only GAUGE or COUNTER.
        #   However, as in that function we do validation that code also
        #   goes here.
        if metric.type is not None and (metric.type != MetricType.GAUGE and
                                        metric.type != MetricType.COUNTER):
            return (False, "Wrong metric type.")

    return (True, "")


def convert_to_prometheus_exposition_format(metrics: List[Metric]) -> str:
    """Convert metrics to the prometheus format."""
    output = []
    curr_time_str = get_current_time()  # adds current timestamp
    for metric in metrics:
        if metric.help is not None:
            output.append('# HELP {0} {1}'.format(
                metric.name, metric.help.replace('\\', r'\\').replace('\n', r'\n')))

        if metric.type is not None:
            output.append('\n# TYPE {0} {1}\n'.format(metric.name, metric.type))

        label_str = '{{{0}}}'.format(','.join(
            ['{0}="{1}"'.format(
             k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
             for k, v in sorted(metric.labels.items())]))

        # https://afterthoughtsoftware.com/posts/python-str-or-repr-on-a-float
        if type(metric.value) == float:
            value_str = repr(float(metric.value))  # here we use repr instead of str
        else:
            value_str = str(metric.value)

        output.append('{0}{1} {2} {3}\n'.format(metric.name, label_str,
                                                value_str, curr_time_str))
    return ''.join(output)


@dataclass
class KafkaStorage(Storage):
    """Storage for saving metrics in Kafka.

    Args:
        brokers_ips:  list of addresses with ports of all kafka brokers (kafka nodes)
        topic: name of a kafka topic where message should be saved
        max_timeout_in_seconds: if a message was not delivered in maximum_timeout seconds
            self.store will throw FailedDeliveryException
    """
    brokers_ips: List[str] = field(default=("127.0.0.1:9092",))
    topic: str = "rmi_metrics"
    max_timeout_in_seconds: float = 0.5  # defaults half of a second

    def __post_init__(self) -> None:
        self._create_producer()

        self.error_from_callback = None
        """used to pass error from within callback_on_delivery
          (called from different thread) to KafkaStorage instance"""

    def _create_producer(self) -> None:
        self.producer = confluent_kafka.Producer(
            {'bootstrap.servers': ",".join(self.brokers_ips)})

    def callback_on_delivery(self, err, msg) -> None:
        """Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush()."""
        if err is not None:
            self.error_from_callback = err
            log.log(logger.ERROR,
                    'KafkaStorage failed to send message; error message: {}'
                    .format(err))
        else:
            log.log(logger.TRACE,
                    'KafkaStorage succeeded to send message; message: {}'
                    .format(msg))

    def store(self, metrics: List[Metric]) -> None:
        """Stores synchronously metrics in kafka.

        The function returns only after sending the message -
        by using synchronous self.producer.flush to block until
        the message (metrics) are delivered to the kafka.

        Raises:
            * UnconvertableToPrometheusExpositionFormat - if metrics are not convertable
                into prometheus exposition format.
            * FailedDeliveryException - if a message could not be written to kafka.
        """

        if not metrics:
            log.warning('Empty list of metrics, store is skipped!')
            return

        is_convertable, error_message = is_convertable_to_prometheus_exposition_format(metrics)
        if not is_convertable:
            log.log(logger.ERROR,
                    'KafkaStorage failed to convert metrics into'
                    'prometheus exposition format; error: "{}"'
                    .format(error_message))
            raise UnconvertableToPrometheusExpositionFormat(error_message)

        msg = convert_to_prometheus_exposition_format(metrics)
        self.producer.produce(self.topic, msg.encode('utf-8'),
                              callback=self.callback_on_delivery)

        r = self.producer.flush(self.max_timeout_in_seconds)  # block until all send

        # check if timeout expired
        if r > 0:
            raise FailedDeliveryException(
                "Maximum timeout {} for sending message has passed out."
                .format(self.max_timeout_in_seconds))

        # check if any failed to be delivered
        if self.error_from_callback is not None:

            # before reseting self.error_from_callback we
            # assign the original value to seperate value
            # to pass it to exception
            error_from_callback__original_ref = self.error_from_callback
            self.error_from_callback = None

            raise FailedDeliveryException(
                "Message has failed to be writen to kafka. API error message: {}."
                .format(error_from_callback__original_ref))

        log.debug('message size=%i stored in kafka topic=%r', len(msg), self.topic)

        return  # the message has been send to kafka
