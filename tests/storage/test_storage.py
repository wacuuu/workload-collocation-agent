import pytest
from unittest import mock

from rmi.metrics import Metric, MetricType
import rmi.storage as storage


@pytest.fixture
def sample_metrics():
    return [
        Metric(name='average_latency_miliseconds', value=8,
               labels={'user': 'felidadae', 'node': 'slave_1'},
               type=MetricType.COUNTER, help='latency measured in miliseconds'),
        Metric(name='percentile_99th_miliseconds', value=89,
               labels={'user': 'felidadae', 'node': 'slave_1'},
               type=MetricType.COUNTER, help='99th percentile in miliseconds')
    ]


@pytest.fixture
def sample_metrics_with_quote():
    """for testing for proper escaping"""
    return [
        Metric(name='average_latency_miliseconds', value=8,
               labels={'user': 'felidadae', 'node': 'slave_1 called "brave heart"'},  # quoted
               type=MetricType.COUNTER, help='latency measured in miliseconds'),
    ]


@pytest.fixture
def sample_metrics_with_float_value():
    """for testing for proper float representation"""
    return [
        Metric(name='average_latency_miliseconds', value=8.223,
               labels={'user': 'felidadae', 'node': 'slave_1'},
               type=MetricType.COUNTER, help='latency measured in miliseconds'),
    ]


# PEC <- prometheus exposition format
@pytest.fixture
def sample_metrics_unconvertable_to_PEF():
    """for testing for proper float representation"""
    return [
        Metric(name='latency-miliseconds', value=8.223,
               labels={'user': 'felidadae', 'node': 'slave_1'},
               type=MetricType.COUNTER, help='latency measured in miliseconds'),
    ]


@mock.patch('rmi.storage.get_current_time', return_value='1531729598000')
def test_convert_to_prometheus_exposition_format(mock_get_current_time, sample_metrics,
                                                 sample_metrics_with_quote,
                                                 sample_metrics_with_float_value):
    msg = storage.convert_to_prometheus_exposition_format(sample_metrics)
    assert(
        msg == (
            '# HELP average_latency_miliseconds latency measured in miliseconds\n'
            '# TYPE average_latency_miliseconds counter\n'
            'average_latency_miliseconds{node="slave_1",user="felidadae"} 8 1531729598000\n'
            '# HELP percentile_99th_miliseconds 99th percentile in miliseconds\n'
            '# TYPE percentile_99th_miliseconds counter\n'
            'percentile_99th_miliseconds{node="slave_1",user="felidadae"} 89 1531729598000\n'
        )
    )

    msg = storage.convert_to_prometheus_exposition_format(sample_metrics_with_quote)
    assert(
        msg == (
            '# HELP average_latency_miliseconds latency measured in miliseconds\n'
            '# TYPE average_latency_miliseconds counter\n'
            'average_latency_miliseconds'  # next string the same line
            '{node="slave_1 called \\"brave heart\\"",user="felidadae"} 8 1531729598000\n'
        )
    )

    msg = storage.convert_to_prometheus_exposition_format(sample_metrics_with_float_value)
    assert(
        msg == (
            '# HELP average_latency_miliseconds latency measured in miliseconds\n'
            '# TYPE average_latency_miliseconds counter\n'
            'average_latency_miliseconds'  # next string the same line
            '{node="slave_1",user="felidadae"} 8.223 1531729598000\n'
        )
    )


@mock.patch('rmi.storage.confluent_kafka.Producer',
            return_value=mock.Mock(flush=mock.Mock(return_value=1)))
def test_when_brocker_unavailable(mock_producer, sample_metrics):
    kafka_storage = storage.KafkaStorage(brokers_ips=["whatever because is ignored"])
    with pytest.raises(storage.FailedDeliveryException, match="Maximum timeout"):
        kafka_storage.store(sample_metrics)
    kafka_storage.producer.flush.assert_called_once()


def test_is_convertable_to_prometheus_exposition_format(
        sample_metrics,
        sample_metrics_with_float_value,
        sample_metrics_unconvertable_to_PEF):
    metric_nPEF = sample_metrics_unconvertable_to_PEF
    is_convertable = storage.is_convertable_to_prometheus_exposition_format

    assert (True, "")  == is_convertable(sample_metrics)
    assert (True, "")  == is_convertable(sample_metrics_with_float_value)
    assert (False, "Wrong metric name latency-miliseconds.") == is_convertable(metric_nPEF)
