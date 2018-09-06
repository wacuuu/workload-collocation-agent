import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

from owca.metrics import Metric, Measurements, MetricType
from owca.mesos import TaskId
from owca.platforms import Platform


# Mapping from task to its measurements.
TasksMeasurements = Dict[TaskId, Measurements]
TasksResources = Dict[TaskId, Dict[str, float]]


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


class Anomaly(ABC):

    @abstractmethod
    def get_metrics(self) -> List[Metric]:
        ...


@dataclass
class ContentionAnomaly(ABC):

    task_ids: List[TaskId]
    resource: ContendedResource

    type = 'contention'

    def get_metrics(self):
        """Encode contention anomaly as list of metrics.

        Anomaly of multiple tasks together, will be encode as many metrics.
        Note, it can return more metrics that provided anomalies because it is necessary
        to encode relation in this way.
        For example:
        anomaly = ContentionAnomaly(tasks_ids=['task1', 'task2'], resource=ContendedResource.LLC)

        wile be encoded as two metrics of type counters:

        metrics = [
            Metric(name='anomaly', type='counter', value=1,
                labels=dict(uuid="1234", task_id="task1", type="contention"))
            Metric(name='anomaly', type='counter', value=1,
                labels=dict(uuid="1234", task_id="task2", type="contention"))
        ]

        Effectively being encoded as in Prometheus format:

        # HELP anomaly ...
        # TYPE anomaly counter
        anomaly(type="contention", task_id="task1", resource="cache", uuid="1234") 1
        anomaly(type="contention", task_id="task2", resource="cache", uuid="1234") 1
        """
        metrics = []
        for task_id in self.task_ids:
            metrics.append(
                Metric(
                    name='anomaly',
                    value=1,
                    type=MetricType.COUNTER,
                    labels=dict(
                        task_id=task_id,
                        resource=self.resource,
                        uuid=self._uuid(),
                        type=self.type,
                    )
                )
            )
        return metrics

    def _uuid(self):
        """Returns unique identifier based on combination of tasks_ids."""
        return _create_uuid_from_tasks_ids(self.task_ids)


class AnomalyDetector(ABC):

    @abstractmethod
    def detect(
            self,
            platform: Platform,
            tasks_measurements: TasksMeasurements,
            tasks_resources: TasksResources,
            ) -> (List[Anomaly], List[Metric]):
        ...


class NOPAnomalyDetector(AnomalyDetector):

    def detect(self, platform, tasks_measurements, tasks_resources):
        return [], []


def convert_anomalies_to_metrics(anomalies: List[Anomaly]) -> List[Metric]:
    """Takes anomalies on input and convert them to something that can be
    stored persistently adding help/type fields and labels.
    """
    metrics = []
    for anomaly in anomalies:
        metrics.extend(anomaly.get_metrics())

    return metrics
