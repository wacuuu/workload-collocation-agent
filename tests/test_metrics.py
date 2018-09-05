import pytest

from owca.mesos import create_metrics
from owca.metrics import Metric
from owca.testing import task


@pytest.mark.parametrize('task,task_measurements,expected_metrics', (
        (task('/t1'),
         {}, []),
        (task('/t1', labels=dict(task_label='task_label_value')), {'cpu': 15},
         [Metric(name='cpu', value=15, labels={'task_id': 'task-id-/t1', 'foo': 'bar',
                                               'task_label': 'task_label_value',
                                               })]),
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
