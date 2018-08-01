import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

from rmi.metrics import Metric, Measurements, MetricType
from rmi.mesos import TaskId
from rmi.platforms import Platform


# Mapping from task to its measurments.
TasksMeasurements = Dict[TaskId, Measurements]


class ContendedResource(str, Enum):

    MEMORY = 'memory bandwidth'
    LLC = 'cache'
    CPUS = 'cpus'


def _create_uuid_from_tasks_ids(task_ids: List[TaskId]):
    """Returns unique identifier based on combination of tasks_ids."""
    # Assumption here that, it is enough to just take
    # 16bytes of 20 for unique different tasks combinations.
    sha1 = hashlib.sha1(','.join(sorted(task_ids)).encode('utf-8')).digest()
    return str(uuid.UUID(bytes=sha1[:16]))


@dataclass
class Anomaly:

    task_ids: List[TaskId]
    resource: ContendedResource

    def uuid(self):
        """Returns unique identifier based on combination of tasks_ids."""
        return _create_uuid_from_tasks_ids(self.task_ids)


class AnomalyDectector(ABC):

    @abstractmethod
    def detect(
            self,
            platform: Platform,
            tasks_measurements: TasksMeasurements) -> (List[Anomaly], List[Metric]):
        ...


class NOPAnomalyDectector(AnomalyDectector):

    def detect(self, platform, tasks_measurements):
        return [], []


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
    metrics = []
    for anomaly in anomalies:
        for task_id in anomaly.task_ids:
            metrics.append(
                Metric(
                    name='anomaly',
                    value=1,
                    type=MetricType.COUNTER,
                    labels=dict(
                        task_id=task_id,
                        resource=anomaly.resource,
                        uuid=anomaly.uuid(),
                    )
                )
            )

    return metrics
