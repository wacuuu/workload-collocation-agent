from dataclasses import dataclass, field
import requests
import urllib.parse

from typing import Dict

# Mesos tasks id
TaskId = str


MESOS_TASK_STATE_RUNNING = 'TASK_RUNNING'
CGROUP_DEFAULT_SUBSYSTEM = 'cpu'


@dataclass
class MesosTask:
    name: str
    workload_id: str

    executor_pid: id
    container_id: str
    task_id: str

    # for debugging purposes
    executor_id: str
    agent_id: str

    # infered
    cgroup_path: str
    labels: Dict[str, str] = field(default_factory=dict)


def find_cgroup(pid):
    with open(f'/proc/{pid}/cgroup') as f:
        for line in f:
            _, subsystems, path = line.strip().split(':')
            subsystems = subsystems.split(',')
            if CGROUP_DEFAULT_SUBSYSTEM in subsystems:
                return path
        else:
            raise Exception(f'Cannot find cgroup mesos path for {pid}')


@dataclass
class MesosNode:

    mesos_agent_endpoint = 'http://127.0.0.1:5051'
    METHOD = 'GET_STATE'
    api_path = '/api/v1'

    def get_tasks(self):
        """ only return running tasks """
        full_url = urllib.parse.urljoin(self.mesos_agent_endpoint, self.api_path)
        r = requests.post(full_url, json=dict(type=self.METHOD))
        r.raise_for_status()
        state = r.json()
        tasks = []

        # Fast return path if there is no any lauched tasks.
        if 'launched_tasks' not in state['get_state']['get_tasks']:
            return tasks

        for launched_task in state['get_state']['get_tasks']['launched_tasks']:
            statuses = launched_task['statuses']
            last_status = statuses[-1]  # Assume the last on is the latest state # TODO: confirm
            if last_status['state'] != MESOS_TASK_STATE_RUNNING:
                continue

            executor_pid = last_status['container_status']['executor_pid']
            cgroup_path = find_cgroup(executor_pid)

            labels = {label['key']: label['value'] for label in launched_task['labels']['labels']}

            for key, value in labels.items():
                if key.endswith('workload_id'):
                    workload_id = value
                    break
            else:
                workload_id = None

            tasks.append(
                MesosTask(
                    name=launched_task['name'],
                    workload_id=workload_id,
                    executor_pid=executor_pid,
                    cgroup_path=cgroup_path,
                    container_id=last_status['container_status']['container_id']['value'],
                    task_id=last_status['task_id']['value'],
                    agent_id=last_status['agent_id']['value'],
                    executor_id=last_status['executor_id']['value'],
                    labels=labels,
                )
            )

        return tasks
