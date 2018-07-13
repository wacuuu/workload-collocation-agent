from dataclasses import dataclass
from typing import List
import logging
import time

from rmi import containers
from rmi import detectors
from rmi import logger
from rmi import mesos
from rmi import platforms
from rmi import storage
from rmi.detectors import TasksMeasurements, Anomaly
from rmi.metrics import Metric

log = logging.getLogger(__name__)


def convert_anomalies_to_metrics(anomalies: List[Anomaly]) -> List[Metric]:
    """Takes anomalies on input and convert them to something that can be
    stored persistently adding help/type fields and labels, including
    correlating Anomaly of multiple tasks together.

    Note, it can return more metrics that provided anomalies because it is necessary
    to encode relation in this way.
    For example:
    anomaly = Anomaly(tasks_ids=['task1', 'task2'], resource=ContendedResource.LLC)

    wile be encoded as two metrics of type counters:

    metrics = [
        Metric(name='anomaly', type='counter', value=1, labels=dict(uuid="1234", task_id="task1"))
        Metric(name='anomaly', type='counter', value=1, labels=dict(uuid="1234", task_id="task2"))
    ]

    Effectively being encoded as in Prometheus format:

    # HELP anomaly ...
    # TYPE anomaly counter
    anomaly(task_id="task1", resource="cache", uuid="1234") 1
    anomaly(task_id="task2", resource="cache", uuid="1234") 1
    """

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

            # Convert tasks to containers.
            # TODO: we should reuse existing containers (those objects are stateful)
            self.containers = [containers.Container(task.cgroup_path) for task in tasks]

            # Sync state of containers TODO: don't create them every time
            for container in self.containers:
                container.sync()

            # Platform information
            platform, platform_metrics, common_labels = platforms.collect_platform_information()

            # Build labeled tasks_metrics and task_metrics_values.
            tasks_measurements: TasksMeasurements = {}
            tasks_metrics: List[Metric] = []
            for container, task in zip(self.containers, tasks):
                task_measurements = container.get_mesurements()
                tasks_measurements[task.task_id] = task_measurements

                task_metrics = []
                for metric_name, metric_value in task_measurements.items():
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
            anomalies, extra_metrics = self.detector.detect(platform, tasks_measurements)

            anomaly_metrics = convert_anomalies_to_metrics(anomalies)
            self.storage.store(anomaly_metrics + extra_metrics)

            if not self.wait_or_finish():
                break

        # cleanup
        for container in self.containers:
            container.cleanup()
