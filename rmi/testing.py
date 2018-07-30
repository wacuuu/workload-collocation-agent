"""Module for independent simple helper functions."""

import os
from io import StringIO

from rmi.detectors import ContendedResource, Anomaly, _create_uuid_from_tasks_ids
from rmi.mesos import MesosTask
from rmi.metrics import Metric, MetricType


def relative_module_path(module_file, relative_path):
    """Returns path relative to current python module."""
    dir_path = os.path.dirname(os.path.realpath(module_file))
    return os.path.join(dir_path, relative_path)


def create_open_mock(sys_file_mock):
    class OpenMock:
        def __init__(self, sys_file):
            self.file_sys = sys_file

        def __call__(self, path):
            return StringIO(self.file_sys[path])

    return OpenMock(sys_file_mock)


def anomaly_metric(task_id, task_ids=None):
    """Helper method to create metric based on anomaly.
    uuid is used if provided.
    """
    return Metric(
                name='anomaly',
                value=1,
                labels=dict(
                    task_id=task_id, resource=ContendedResource.MEMORY,
                    uuid=_create_uuid_from_tasks_ids(task_ids or [task_id])),
                type=MetricType.COUNTER
            )


def anomaly(task_ids):
    """Helper method to create simple anomaly for single task.
    It is always about memory contention."""
    return Anomaly(
        task_ids=task_ids,
        resource=ContendedResource.MEMORY,
    )


def task(cgroup_path):
    """Helper method to create task with default values."""
    return MesosTask(
        cgroup_path=cgroup_path,
        name='name-' + cgroup_path,
        executor_pid=1,
        container_id='container_id-' + cgroup_path,
        task_id='task-id-' + cgroup_path,
        executor_id='executor-id-' + cgroup_path,
        agent_id='agent-id-' + cgroup_path,
    )
