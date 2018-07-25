import logging
import os

from rmi.metrics import Measurements

BASE_SUBSYSTEM_PATH = '/sys/fs/cgroup/cpu'
BASE_RESCTRL_PATH = '/sys/fs/resctrl'
TASKS_FILENAME = 'tasks'
CPUS_FILENAME = 'cpus'
MON_DATA = 'mon_data'
MBM_TOTAL = 'mbm_total_bytes'
CPU_USAGE = 'cpuacct.usage'


log = logging.getLogger(__name__)


class ResGroup:

    def __init__(self, cgroup_path):
        assert cgroup_path.startswith('/'), 'Provide cgroup_path with leading /'
        relative_cgroup_path = cgroup_path[1:]  # cgroup path without leading '/'
        self.cgroup_fullpath = os.path.join(
            BASE_SUBSYSTEM_PATH, relative_cgroup_path)
        # Resctrl group is flat so flatten then cgroup hierarchy.
        flatten_rescgroup_name = relative_cgroup_path.replace('/', '-')
        self.resgroup_dir = os.path.join(BASE_RESCTRL_PATH, flatten_rescgroup_name)
        self.resgroup_tasks = os.path.join(self.resgroup_dir, TASKS_FILENAME)

    def sync(self):
        """Copy all the tasks from all cgroups to resctrl tasks file
        """
        if not os.path.exists('/sys/fs/resctrl'):
            log.warning('Resctrl not mounted, ignore sync!')
            return

        tasks = ''
        with open(os.path.join(self.cgroup_fullpath, TASKS_FILENAME)) as f:
            tasks += f.read()

        os.makedirs(self.resgroup_dir, exist_ok=True)
        with open(self.resgroup_tasks, 'w') as f:
            for task in tasks.split():
                f.write(task)
                f.flush()

    def get_measurements(self) -> Measurements:
        """
        mbm_total: Memory bandwidth - type: counter, unit: [bytes]
        cpu_usage: Cpu usage - type: counter, unit: [ns]
        :return: Dictionary containing memory bandwidth
        and cpu usage measurements
        """
        mbm_total = 0

        # mon_dir contains event files for specific socket:
        # llc_occupancy, mbm_total_bytes, mbm_local_bytes
        for mon_dir in os.listdir(os.path.join(self.resgroup_dir, MON_DATA)):
            with open(os.path.join(self.resgroup_dir, MON_DATA,
                                   mon_dir, MBM_TOTAL)) as mbm_total_file:
                mbm_total += int(mbm_total_file.read())

        with open(os.path.join(self.cgroup_fullpath, CPU_USAGE)) as \
                cpu_usage_file:
            cpu_usage = int(cpu_usage_file.read())

        return dict(memory_bandwidth=mbm_total, cpu_usage=cpu_usage)

    def cleanup(self):
        os.rmdir(self.resgroup_dir)
