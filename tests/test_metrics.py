import pytest

from owca.mesos import create_metrics, sanitize_mesos_label
from owca.metrics import Metric


@pytest.mark.parametrize('label_key,expected_label_key', (
    ('org.apache.ble', 'ble'),
    ('org.apache.aurora.metadata.foo', 'foo'),
    ('some.dots.found', 'some_dots_found'),
))
def test_sanitize_labels(label_key, expected_label_key):
    assert sanitize_mesos_label(label_key) == expected_label_key


@pytest.mark.parametrize('task_measurements,expected_metrics', (
        ({}, []),
        ({'cpu': 15},
         [Metric(name='cpu', value=15)]),
        ({'cpu': 15, 'ram': 30},
         [
             Metric(name='cpu', value=15),
             Metric(name='ram', value=30)
         ]),
))
def test_create_metrics(task_measurements, expected_metrics):
    got_metrics = create_metrics(task_measurements)
    assert expected_metrics == got_metrics
