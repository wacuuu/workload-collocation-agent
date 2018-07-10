from rmi import config
from rmi import detectors
from rmi import mesos
from rmi import runner
from rmi import storage

from typing import List


def register_components(extra_components: List[str]):
    config.register(runner.DetectionRunner)
    config.register(mesos.MesosNode)
    config.register(storage.LogStorage)
    config.register(detectors.NOPAnomalyDectector)

    for component in extra_components:
        cls = __import__(component)  # TODO: proper resolution use pkg_resourse resoleving
        config.register(cls)
