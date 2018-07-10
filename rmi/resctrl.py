import os

BASE_SUBSYSTEM_PATH = '/sys/fs/cgroup/cpu'
BASE_RESCTRL_PATH = '/sys/fs/resctrl'
TASKS_FILENAME = 'tasks'


class ResGroup:

    def __init__(self, cgroup_path):
        self.cgroup_path = cgroup_path
        self.resctrl_path = cgroup_path.replace('/', '-')

    def sync(self):
        """Copy all the tasks from all cgroups to resctrl tasks file
        """
        tasks = ''
        for cgroup in self.cgroups:
            cgroup_fullpath = os.path.join(BASE_SUBSYSTEM_PATH, cgroup, TASKS_FILENAME)
            with open(cgroup_fullpath) as f:
                tasks += f.read()

        resctrl_fullpath = os.path.join(BASE_RESCTRL_PATH, self.resctrl_path, TASKS_FILENAME)

        with open(resctrl_fullpath) as f:
            for task in tasks.split():
                f.write(task)
                f.flush()

    def get_metrics(self):
        # TODO: implement me
        return dict(cache_usage=50)
