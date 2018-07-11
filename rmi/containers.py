from typing import List, Dict, Union

from rmi.resctrl import ResGroup
from rmi.cgroups import Cgroup
from rmi.perf import PerfCounters
from rmi.metrics import MetricValues


DEFAULT_EVENTS = ('instructions', 'cycles', 'cache_misses')


def flatten_metrics(metrics: List[MetricValues]):
    all_metrics_flat = dict()

    for metric_values in metrics:
        assert not set(metric_values.keys()) & set(all_metrics_flat).keys(), \
            'When flatinng metrics the keys should not overlap!'
        all_metrics_flat.update(metric_values)
    return all_metrics_flat


class Container:

    def __init__(self, cgroup_path):
        self.cgroup = Cgroup(cgroup_path)
        self.resgroup = ResGroup(cgroup_path)
        self.perf_counters = PerfCounters(cgroup_path, events=DEFAULT_EVENTS)

    def sync(self):
        self.resctrl.sync()

    def get_metrics(self) -> Dict[str, Union[float, int]]:
        return flatten_metrics([
            self.cgroup.get_metrics(),
            self.resgroup.get_metrics(),
            self.perf_counters.get_metrics(),
        ])
