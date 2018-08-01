import os

from dataclasses import dataclass

from rmi.metrics import Measurements, MetricName


CPU_USAGE = 'cpuacct.usage'
BASE_SUBSYSTEM_PATH = '/sys/fs/cgroup/cpu'


@dataclass
class Cgroup:

    cgroup_path: str

    def __post_init__(self):
        assert self.cgroup_path.startswith('/'), 'Provide cgroup_path with leading /'
        relative_cgroup_path = self.cgroup_path[1:]  # cgroup path without leading '/'
        self.cgroup_fullpath = os.path.join(BASE_SUBSYSTEM_PATH, relative_cgroup_path)

    def get_measurements(self) -> Measurements:

        with open(os.path.join(self.cgroup_fullpath, CPU_USAGE)) as \
                cpu_usage_file:
            cpu_usage = int(cpu_usage_file.read())

        return {MetricName.CPU_USAGE_PER_TASK: cpu_usage}
