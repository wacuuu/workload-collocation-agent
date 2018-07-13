import os

from rmi.metrics import Measurements

BASE_SUBSYSTEM_PATH = '/sys/fs/cgroup/cpu'
BASE_RESCTRL_PATH = '/sys/fs/resctrl'
TASKS_FILENAME = 'tasks'


class ResGroup:

    def __init__(self, cgroup_path):
        assert cgroup_path.startswith('/'), 'Provide cgroup_path with leading /'
        relative_cgroup_path = cgroup_path[1:]  # cgroup path without leading '/'
        self.cgroup_fullpath = os.path.join(
            BASE_SUBSYSTEM_PATH, relative_cgroup_path, TASKS_FILENAME)
        # Resctrl group is flat so flatten then cgroup hierarchy.
        flatten_rescgroup_name = relative_cgroup_path.replace('/', '-')
        self.resgroup_dir = os.path.join(BASE_RESCTRL_PATH, flatten_rescgroup_name)
        self.resgroup_tasks = os.path.join(self.resgroup_dir, TASKS_FILENAME)

    def sync(self):
        """Copy all the tasks from all cgroups to resctrl tasks file
        """
        tasks = ''
        with open(self.cgroup_fullpath) as f:
            tasks += f.read()

        os.makedirs(self.resgroup_dir, exist_ok=True)
        with open(self.resgroup_tasks) as f:
            for task in tasks.split():
                f.write(task)
                f.flush()

    def get_measurements(self) -> Measurements:
        # TODO: implement me
        return dict(cache_usage=50)

    def cleanup(self):
        os.rmdir(self.resgroup_dir)
