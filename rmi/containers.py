from typing import List, Dict, Union

from rmi.resctrl import ResGroup
from rmi.cgroups import Cgroup
from rmi.perf import PerfCounters


def merge_metrics(metrics: List[dict]):
    d = dict()
    [d.update(m) for m in metrics]
    return d


class Container:

    def __init__(self, cgroup_path):
        self.cgroup = Cgroup(cgroup_path)
        self.resctrl = ResGroup(cgroup_path)
        self.perf_counters = PerfCounters(cgroup_path)

    def sync(self):
        self.resctrl.sync()

    def get_metrics(self) -> Dict[str, Union[float, int]]:
        return merge_metrics(
            self.cgroup.get_metrics(),
            self.resgroup.get_metrics(),
            self.perf_counters.get_metrics(),
        )
