"""
Module is responsible for exposing  functionality of storing labeled metrics
in durable external storage.
"""
import abc
import logging
from typing import List

from rmi.metrics import Metric

log = logging.getLogger(__name__)


class Storage(abc.ABC):

    @abstractmethod
    def store(self, metrics: List[Metric]):
        """store metrics """
        ...


class LogStorage(Storage):

    def store(self, metrics):
        log.debug(metrics)
