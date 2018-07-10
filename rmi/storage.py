"""
Module is responsible for exposing  functionallity of storing labeled metrics
in durable external storage.
"""
import abc
import logging
from typing import List
from rmi.base import Metric

log = logging.getLogger(__name__)


class Storage(abc.ABC):

    def store(self, metrics: List[Metric]):
        """store metrics """
        ...


class LogStroage(Storage):
    def store(self, metrics):
        log.debug(metrics)
