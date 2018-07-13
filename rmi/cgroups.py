from dataclasses import dataclass

from rmi.metrics import Measurements


@dataclass
class Cgroup:

    cgroup_path: str

    def get_measurements(self) -> Measurements:
        # TODO: implement me
        return {'cpu_usage': 17}
