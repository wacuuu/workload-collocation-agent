from typing import Dict

from rmi.metrics import MetricValues


class Cgroup:

    def __init__(self, cgroup_path):
        self.cgroup_path = cgroup_path

    def get_metrics(self) -> MetricValues:
        # TODO: implement me
        return {}
