from typing import List
import pkg_resources

from rmi import config
from rmi import detectors
from rmi import mesos
from rmi import runner
from rmi import storage


def register_components(extra_components: List[str]):
    config.register(runner.DetectionRunner)
    config.register(mesos.MesosNode)
    config.register(storage.LogStorage)
    config.register(storage.KafkaStorage)
    config.register(detectors.NOPAnomalyDectector)

    for component in extra_components:
        # Load external class ignored its requirements.
        ep = pkg_resources.EntryPoint.parse('external_cls=%s' % component)
        cls = ep.load(require=False)
        config.register(cls)
