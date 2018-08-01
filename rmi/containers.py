from typing import List

from dataclasses import dataclass

from rmi.resctrl import ResGroup
from rmi.cgroups import Cgroup
from rmi.perf import PerfCounters
from rmi.metrics import Measurements, MetricName


DEFAULT_EVENTS = (MetricName.INSTRUCTIONS, MetricName.CYCLES, MetricName.CACHE_MISSES)


def flatten_measurements(measurements: List[Measurements]):
    all_measurements_flat = dict()

    for measurement in measurements:
        assert not set(measurement.keys()) & set(all_measurements_flat.keys()), \
            'When flatting measurements the keys should not overlap!'
        all_measurements_flat.update(measurement)
    return all_measurements_flat


@dataclass
class Container:

    cgroup_path: str
    rdt_enabled: bool = True

    def __post_init__(self):
        self.cgroup = Cgroup(self.cgroup_path)
        self.perf_counters = PerfCounters(self.cgroup_path, event_names=DEFAULT_EVENTS)
        self.resgroup = ResGroup(self.cgroup_path) if self.rdt_enabled else None

    def sync(self):
        if self.rdt_enabled:
            self.resgroup.sync()

    def get_measurements(self) -> Measurements:
        return flatten_measurements([
            self.cgroup.get_measurements(),
            self.resgroup.get_measurements() if self.rdt_enabled else {},
            self.perf_counters.get_measurements(),
        ])

    def cleanup(self):
        if self.rdt_enabled:
            self.resgroup.cleanup()
        self.perf_counters.cleanup()
