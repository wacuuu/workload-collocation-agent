import pytest
from unittest.mock import patch, Mock

from owca.runner import _calculate_desired_state, DetectionRunner
from owca.mesos import MesosNode
from owca.containers import Container
from owca import storage
from owca import platforms
from owca.metrics import Metric
from owca.detectors import AnomalyDetector
from owca.testing import anomaly_metric, anomaly, task


def container(cgroup_path):
    """Helper method to create container with patched subsystems."""
    with patch('owca.containers.ResGroup'), patch('owca.containers.PerfCounters'):
        return Container(cgroup_path, rdt_enabled=False)


def metric(name):
    """Helper method to create metric with default values. Value is ignored during tests."""
    return Metric(name=name, value=1234)


@pytest.mark.parametrize(
    'discovered_tasks,containers,expected_new_tasks,expected_containers_to_delete', (
        # scenario when two task are created and them first one is removed,
        ([task('/t1')], [],  # one new task, just arrived
         [task('/t1')], []),  # should created one container
        ([task('/t1')], [container('/t1')],  # after one iteration, our state is converged
         [], []),  # no actions
        ([task('/t1'), task('/t2')], [container('/t1'), ],  # another task arrived,
         [task('/t2')], []),  # let's create another container,
        ([task('/t1'), task('/t2')], [container('/t1'), container('/t2')],  # 2on2 converged
         [], []),  # nothing to do,
        ([task('/t2')], [container('/t1'), container('/t2')],  # first task just disappeared
         [], [container('/t1')]),  # remove the first container
        # some other cases
        ([task('/t1'), task('/t2')], [],  # the new task, just appeared
         [task('/t1'), task('/t2')], []),
        ([task('/t1'), task('/t3')], [container('/t1'),
                                      container('/t2')],  # t2 replaced with t3
         [task('/t3')], [container('/t2')]),  # nothing to do,
    ))
def test_calculate_desired_state(
        discovered_tasks,
        containers,
        expected_new_tasks,
        expected_containers_to_delete):

    new_tasks, containers_to_delete = _calculate_desired_state(
        discovered_tasks, containers
    )

    assert new_tasks == expected_new_tasks
    assert containers_to_delete == expected_containers_to_delete


@patch('owca.containers.ResGroup')
@patch('owca.containers.PerfCounters')
@patch('owca.containers.Container.sync')
@patch('owca.containers.Container.cleanup')
@pytest.mark.parametrize('tasks,existing_containers,expected_running_containers', (
    ([], {},
     {}),
    ([task('/t1')], {},
     {task('/t1'): container('/t1')}),
    ([task('/t1')], {task('/t2'): container('/t2')},
     {task('/t1'): container('/t1')}),
    ([task('/t1')], {task('/t1'): container('/t1'), task('/t2'): container('/t2')},
     {task('/t1'): container('/t1')}),
    ([], {task('/t1'): container('/t1'), task('/t2'): container('/t2')},
     {}),
))
def test_sync_containers_state(cleanup_mock, sync_mock, PerfCoutners_mock, ResGroup_mock,
                               tasks, existing_containers,
                               expected_running_containers):

    # Mocker runner, because we're only interested in one sync_containers_state function.
    runner = DetectionRunner(
        node=Mock(),
        metrics_storage=Mock(),
        anomalies_storage=Mock(),
        detector=Mock(),
        rdt_enabled=False,
    )
    # Prepare internal state used by sync_containers_state function.
    runner.containers = dict(existing_containers)  # Use list for copying to have original list.

    # Call it.
    runner._sync_containers_state(tasks)

    # Check internal state ...
    assert expected_running_containers == runner.containers

    # Check other side effects like calling sync() on external objects.
    assert sync_mock.call_count == len(expected_running_containers)
    number_of_removed_containers = len(set(existing_containers) - set(expected_running_containers))
    assert cleanup_mock.call_count == number_of_removed_containers


# We are mocking objects used by containers.
@patch('owca.runner.are_privileges_sufficient', return_value=True)
@patch('owca.containers.ResGroup')
@patch('owca.containers.PerfCounters')
@patch('owca.containers.Cgroup.get_measurements', return_value=dict(cpu_usage=23))
def test_runner_containers_state(get_measurements_mock, PerfCounters_mock,
                                 ResGroup_mock, are_privileges_sufficient_mock):
    """Tests proper interaction between runner instance and functions for
    creating anomalies and calculating the desired state.
    """

    node_mock = Mock(spec=MesosNode, get_tasks=Mock(return_value=[
        task('/t1', resources=dict(cpus=8.))]))
    metrics_storage = Mock(spec=storage.Storage, store=Mock())
    anomalies_storage = Mock(spec=storage.Storage, store=Mock())

    # simulate returning one anomaly and additional metric
    detector_mock = Mock(spec=AnomalyDetector,
                         detect=Mock(return_value=(
                             [anomaly(['task1'])],
                             [metric('bar')])))

    runner = DetectionRunner(
        node=node_mock,
        metrics_storage=metrics_storage,
        anomalies_storage=anomalies_storage,
        detector=detector_mock,
        rdt_enabled=False,
    )

    # Mock to finish after one iteration.
    runner.wait_or_finish = Mock(return_value=False)

    platform_mock = Mock(spec=platforms.Platform)
    with patch('owca.platforms.collect_platform_information', return_value=(
            platform_mock, [metric('platform-cpu-usage')], {})):
        runner.run()

    # store() method was called twice:
    # 1. Before calling detect() to store state of the environment.
    # 2. After calling detect to store information about detected anomalies.
    metrics_storage.store.called_once_with(
            metric('platform-cpu-usage'),  # Store metrics from platform ...
            Metric(name='cpu_usage', value=23, labels={'task_id': 'task-id-/t1'}))  # and task
    anomalies_storage.store.called_once_with(
            anomaly_metric('task1'),
            metric('bar'))  # Store with metrics returned from detector + anomaly.

    # Check that detector was called with proper arguments.
    detector_mock.detect.assert_called_once_with(
        platform_mock,
        {'task-id-/t1': {'cpu_usage': 23}},
        {'task-id-/t1': {'cpus': 8}}
    )

    # assert expected state (new container based on first task /t1)
    assert runner.containers == {task('/t1', resources=dict(cpus=8.)): container('/t1')}

    runner.wait_or_finish.assert_called_once()
