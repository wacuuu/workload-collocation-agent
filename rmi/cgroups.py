from dataclasses import dataclass

from rmi.metrics import MetricValues


@dataclass
class Cgroup:

    cgroup_path: str

    def get_metrics(self) -> MetricValues:
        # TODO: implement me
        return {}
