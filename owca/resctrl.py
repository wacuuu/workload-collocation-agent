import logging
import os

from owca.cgroups import BASE_SUBSYSTEM_PATH
from owca.metrics import Measurements, MetricName

BASE_RESCTRL_PATH = '/sys/fs/resctrl'
TASKS_FILENAME = 'tasks'
SCHEMATA = 'schemata'
INFO = 'info'
MON_DATA = 'mon_data'
MON_L3_00 = 'mon_L3_00'
MBM_TOTAL = 'mbm_total_bytes'
LLC_OCCUPANCY = 'llc_occupancy'


log = logging.getLogger(__name__)


def check_resctrl():
    """
    :return: True if resctrl is mounted and has required file
             False if resctrl is not mounted or required file is missing
    """
    run_anyway_text = 'If you wish to run script anyway,' \
                      'please set rdt_enabled to False in configuration file.'

    resctrl_tasks = os.path.join(BASE_RESCTRL_PATH, TASKS_FILENAME)
    try:
        with open(resctrl_tasks):
            pass
    except IOError as e:
        log.debug('Error: Failed to open %s: %s', resctrl_tasks, e)
        log.critical('Resctrl not mounted. ' + run_anyway_text)
        return False

    mon_data = os.path.join(BASE_RESCTRL_PATH, MON_DATA, MON_L3_00, MBM_TOTAL)
    try:
        with open(mon_data):
            pass
    except IOError as e:
        log.debug('Error: Failed to open %s: %s', mon_data, e)
        log.critical('Resctrl does not support Memory Bandwidth Monitoring.' +
                     run_anyway_text)
        return False

    return True


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
        :return: Dictionary containing memory bandwidth
        and cpu usage measurements
        """
        mbm_total = 0
        llc_occupancy = 0

        # mon_dir contains event files for specific socket:
        # llc_occupancy, mbm_total_bytes, mbm_local_bytes
        for mon_dir in os.listdir(os.path.join(self.resgroup_dir, MON_DATA)):
            with open(os.path.join(self.resgroup_dir, MON_DATA,
                                   mon_dir, MBM_TOTAL)) as mbm_total_file:
                mbm_total += int(mbm_total_file.read())
            with open(os.path.join(self.resgroup_dir, MON_DATA,
                                   mon_dir, LLC_OCCUPANCY)) as llc_occupancy_file:
                llc_occupancy += int(llc_occupancy_file.read())

        return {MetricName.MEM_BW: mbm_total, MetricName.LLC_OCCUPANCY: llc_occupancy}

    def cleanup(self):
        os.rmdir(self.resgroup_dir)
