from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

from rmi.metrics import Metric, Measurements
from rmi.mesos import TaskId
from rmi.platforms import Platform


# Mapping from task to its measurments.
TasksMeasurements = Dict[TaskId, Measurements]


class ContendedResource(Enum):

    MEMORY = 'memory bandwidth'
    LLC = 'cache'
    CPUS = 'cpus'


@dataclass
class Anomaly:

    task_ids: List[TaskId]
    resource: ContendedResource

    def uuid(self):
        # TODO: uniq combintation of tasks ids as uuid
        return 'foo-uuid'


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
