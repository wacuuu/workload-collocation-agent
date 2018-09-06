from dataclasses import dataclass, field
from typing import Dict, List
import urllib.parse
import logging

import requests

# Mesos tasks id
from owca.metrics import Measurements, Metric

TaskId = str


MESOS_TASK_STATE_RUNNING = 'TASK_RUNNING'
CGROUP_DEFAULT_SUBSYSTEM = 'cpu'

log = logging.getLogger(__name__)


@dataclass
class MesosTask:
    name: str

    executor_pid: int
    container_id: str  # Mesos containerizer identifier "ID used to uniquely identify a container"
    task_id: TaskId  # Mesos-level task identifier

    # for debugging purposes
    executor_id: str
    agent_id: str

    # inferred
    cgroup_path: str  # Starts with leading "/"
    labels: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        """Every instance of mesos task is uniqully identified by cgroup_path.
        Assumption here is that every mesos task is represented by one main cgroup.
        """
        return id(self.cgroup_path)


def find_cgroup(pid):
    """ Returns cgroup_path relative to 'cpu' subsystem based on /proc/{pid}/cgroup
    with leading '/'"""

    with open(f'/proc/{pid}/cgroup') as f:
        for line in f:
            _, subsystems, path = line.strip().split(':')
            subsystems = subsystems.split(',')
            if CGROUP_DEFAULT_SUBSYSTEM in subsystems:
                return path
        else:
            raise Exception(f'Cannot find cgroup mesos path for {pid}')


@dataclass
class MesosNode:

    mesos_agent_endpoint = 'http://127.0.0.1:5051'
    METHOD = 'GET_STATE'
    api_path = '/api/v1'

    def get_tasks(self):
        """ only return running tasks """
        full_url = urllib.parse.urljoin(self.mesos_agent_endpoint, self.api_path)
        r = requests.post(full_url, json=dict(type=self.METHOD))
        r.raise_for_status()
        state = r.json()
        tasks = []

        # Fast return path if there is no any launched tasks.
        if 'launched_tasks' not in state['get_state']['get_tasks']:
            return []

        for launched_task in state['get_state']['get_tasks']['launched_tasks']:
            statuses = launched_task['statuses']
            last_status = statuses[-1]  # Assume the last on is the latest state # TODO: confirm
            if last_status['state'] != MESOS_TASK_STATE_RUNNING:
                continue

            if 'executor_pid' not in last_status['container_status']:
                log.warning("'executor_pid' not found in container status for task %s on agent %s",
                            last_status['task_id']['value'],
                            last_status['agent_id']['value'])
                continue

            executor_pid = last_status['container_status']['executor_pid']
            cgroup_path = find_cgroup(executor_pid)

            labels = {label['key']: label['value'] for label in launched_task['labels']['labels']}

            tasks.append(
                MesosTask(
                    name=launched_task['name'],
                    executor_pid=executor_pid,
                    cgroup_path=cgroup_path,
                    container_id=last_status['container_status']['container_id']['value'],
                    task_id=last_status['task_id']['value'],
                    agent_id=last_status['agent_id']['value'],
                    executor_id=last_status['executor_id']['value'],
                    labels=labels,
                )
            )

        return tasks


MESOS_LABELS_PREFIXES_TO_DROP = ('org.apache.', 'aurora.metadata.')


def sanitize_mesos_label(label_key):
    """Removes unwanted prefixes from Aurora & Mesos e.g. 'org.apache.aurora'
    and replaces invalid characters like "." with underscore.
    """
    # Drop unwanted prefixes
    for unwanted_prefix in MESOS_LABELS_PREFIXES_TO_DROP:
        if label_key.startswith(unwanted_prefix):
            label_key = label_key.replace(unwanted_prefix, '')

    # Prometheus labels cannot contain ".".
    label_key = label_key.replace('.', '_')

    return label_key


def create_metrics(
        task: MesosTask,
        task_measurements: Measurements,
        common_labels: Dict[str, str]) -> List[Metric]:
    """Prepare a list of metrics for a mesos tasks based on provided measurements
    applying common_labels.
    :param task: use information from MesosTask to decorate metrics with labels
    :param task_measurements: use values of measurements to create metrics
    :param common_labels: apply those labels to every created metric
    """
    metrics = []
    for metric_name, metric_value in task_measurements.items():
        metric = Metric.create_metric_with_metadata(name=metric_name, value=metric_value)

        # Common labels
        metric.labels.update(common_labels)

        # Task labels
        metric.labels.update(dict(
            task_id=task.task_id,
        ))
        metric.labels.update(task.labels)

        # Sanitaize Mesos labels (containing dots) before passing to Prometheus.
        metric.labels = {
            sanitize_mesos_label(label_key): label_value
            for label_key, label_value
            in metric.labels.items()
        }

        metrics.append(metric)
    return metrics
