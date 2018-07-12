from dataclasses import dataclass
from typing import List
import logging
import time

from rmi import mesos
from rmi import logger
from rmi import storage
from rmi import containers
from rmi import platforms
from rmi import detectors
from rmi.metrics import Metric, MetricValues

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
    node: mesos.MesosNode
    storage: storage.Storage
    detector: detectors.AnomalyDectector
    action_delay: float = 0.  # [s]

    def __post_init__(self):
        self.node = self.node or mesos.MesosNode()
        self.containers = []

    def wait_or_finish(self):
        """Decides how long one run takes and when to finish.
        TODO: handle graceful shutdown on signal
        """
        time.sleep(self.action_delay)
        return True

    @logger.trace(log)
    def run(self):

        while True:

            # Collect information about tasks running on node.
            tasks = self.node.get_tasks()

            # Convert tasks to containers and collect all metrics.
            self.containers = [containers.Container(task.cgroup_path) for task in tasks]

            # Sync state of containers TODO: don't create them every time
            for container in self.containers:
                container.sync()

            # Platform information
            platform, platform_metrics, common_labels = platforms.collect_platform_information()

            # Build labeled tasks_metrics and task_metrics_values.
            tasks_metrics: List[Metric] = []
            for container, task in zip(self.containers, tasks):
                task_metric_values: MetricValues = container.get_metrics()
                task_metrics: List[Metric] = []
                for metric_name, metric_value in task_metric_values.items():

                    metric = Metric(
                        name=metric_name,
                        value=metric_value,
                        # TODO: help & type
                    )

                    metric.labels.update(dict(
                        task_id=task.task_id,  # TODO: add all necessary labels
                    ))
                    metric.labels.update(common_labels)
                tasks_metrics += task_metrics

            self.storage.store(platform_metrics + tasks_metrics)

            # Wrap tasks with metrics
            tasks_metric_values = extract_tasks_value_metrics(task_metrics)
            anomalies, extra_metrics = self.detector.detect(platform, tasks_metric_values)

            anomaly_metrics = convert_anomalies_to_metrics(anomalies)
            self.storage.store(anomaly_metrics + extra_metrics)

            if not self.wait_or_finish():
                break

        # cleanup
        for container in self.containers:
            container.cleanup()
