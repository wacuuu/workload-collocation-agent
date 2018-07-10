import logging

from dataclasses import dataclass

from rmi import mesos
from rmi import storage
from rmi import containers
from rmi import platforms
from rmi import detectors
from rmi import base

log = logging.getLogger(__name__)


def extract_tasks_value_metrics(task_metrics):
    #  TODO: implement me
    return {}


def convert_anomalies_to_metrics(anomalies):
    #  TODO: implement me
    return []


@dataclass
class DetectionRunner:
    """Watch over tasks running on this cluster on this node, collect observation
    and report externally (using storage) detected anomalies.
    """
    node = mesos.MesosNode()
    storage: storage.Storage = storage.LogStorge()
    action_delay: float = 0.  # [s]
    detection: base.AnomalyDectector = detectors.NOPAnomalyDetector

    def __post_init__(self):
        self.node = self.node or mesos.MesosNode()

    def run(self):

        platform = base.Platform()

        while True:

            # Collect information about tasks running on node.
            tasks = self.node.get_tasks()

            # Convert tasks to containers and collect all metrics.
            containers = [containers.Container(task.cgroup_path) for task in tasks]

            # Platform information
            platform = platform.collect_platform_information()
            platform, platform_metrics, common_labels = platforms.collect_platform_information()

            # Build labeleds tasks_metrics and task_metrics_values.
            tasks_metrics = []
            for container, task in zip(containers, tasks):
                task_metrics = container.get_metrics()
                for metric in task_metrics.values():
                    metric.labels.update(dict(
                        job_id=task.job_id,  # TODO: add all neseseary labels
                    ))
                    metric.lables.update(common_labels)
                tasks_metrics += task_metrics

            storage.store(platform_metrics + tasks_metrics)

            # Wrap tasks with metrics
            tasks_metric_values = []
            anomalies, metrics = self.detection.detect(platform, tasks_metric_values)

            anomaly_metrics = convert_anomalies_to_metrics(anomalies)
            storage.store(anomaly_metrics + metrics)
