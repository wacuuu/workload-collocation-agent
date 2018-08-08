import pytest

from rmi.mesos import create_metrics
from rmi.metrics import Metric
from rmi.testing import task


@pytest.mark.parametrize('task,task_measurements,expected_metrics', (
        (task('/t1'),
         {}, []),
        (task('/t1'), {'cpu': 15},
         [Metric(name='cpu', value=15, labels={'task_id': 'task-id-/t1', 'foo': 'bar'})]),
        (task('/t1'), {'cpu': 15, 'ram': 30},
         [
             Metric(name='cpu', value=15, labels={'task_id': 'task-id-/t1', 'foo': 'bar'}),
             Metric(name='ram', value=30, labels={'task_id': 'task-id-/t1', 'foo': 'bar'})
         ]),
))
def test_create_metrics(task, task_measurements, expected_metrics):
    common_labels = {'foo': 'bar'}
    got_metrics = create_metrics(task, task_measurements, common_labels)
    assert expected_metrics == got_metrics
