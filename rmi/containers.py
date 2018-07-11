from typing import List

from rmi.resctrl import ResGroup
from rmi.cgroups import Cgroup
from rmi.perf import PerfCounters
from rmi.metrics import Measurements, MetricName


DEFAULT_EVENTS = (MetricName.INSTRUCTIONS, MetricName.CYCLES, MetricName.LLC_MISSES)


def flatten_measurements(measurements: List[Measurements]):
    all_measurements_flat = dict()

    for measurement in measurements:
        assert not set(measurement.keys()) & set(all_measurements_flat.keys()), \
            'When flatting measurments the keys should not overlap!'
        all_measurements_flat.update(measurement)
    return all_measurements_flat


class Container:

    def __init__(self, cgroup_path):
        self.cgroup = Cgroup(cgroup_path)
        self.resgroup = ResGroup(cgroup_path)
        self.perf_counters = PerfCounters(cgroup_path, event_names=DEFAULT_EVENTS)

    def sync(self):
        self.resgroup.sync()

    def get_mesurements(self) -> Measurements:
        return flatten_measurements([
            self.cgroup.get_measurements(),
            self.resgroup.get_measurements(),
            self.perf_counters.get_measurements(),
        ])

    def cleanup(self):
        self.resgroup.cleanup()
        self.perf_counters.cleanup()
