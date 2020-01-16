from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs

GB = 1000 ** 3
MB = 1000 ** 2

TaskId = str
NodeId = int
Assignments = Dict[TaskId, NodeId]


class Resources:
    def __init__(self, cpu, mem, membw):
        self.cpu = cpu
        self.mem = mem
        self.membw = membw

    @staticmethod
    def create_empty():
        return Resources(0, 0, 0)

    def __repr__(self):
        return str({'cpu': self.cpu, 'mem': float(self.mem) / float(GB),
                    'membw': float(self.membw) / float(GB)})

    def __bool__(self):
        return self.cpu >= 0 and self.mem >= 0 and self.membw >= 0

    def substract(self, b):
        self.cpu -= b.cpu
        self.mem -= b.mem
        self.membw -= b.membw

    def copy(self):
        return Resources(self.cpu, self.mem, self.membw)


class Task:
    def __init__(self, name, initial, assignment=None):
        self.name = name
        self.initial = initial
        self.assignment = assignment

        self.real = Resources.create_empty()
        self.life_time = 0

    def update(self, delta_time):
        """Update state of task when it becomes older by delta_time."""
        self.life_time += delta_time
        # Here simply just if, life_time > 0 assign all
        self.real = self.initial.copy()

    def __repr__(self):
        return "(name: {}, assignment: {}, initial: {}, real: {})".format(
            self.name, 'None' if self.assignment is None else self.assignment.name,
            str(self.initial), str(self.real))


class Node:
    def __init__(self, name, resources):
        self.name = name
        self.initial = resources
        self.real = resources.copy()
        self.unassigned = resources.copy()

    def __repr__(self):
        return "(name: {}, unassigned: {}, initial: {}, real: {})".format(
            self.name, str(self.unassigned), str(self.initial), str(self.real))

    def validate_assignment(self, tasks, new_task):
        """if unassigned > free_not_unassigned"""
        unassigned = self.initial.copy()
        for task in tasks:
            if task.assignment == self:
                unassigned.substract(task.initial)
        unassigned.substract(new_task.initial)
        return bool(unassigned)

    def update(self, tasks):
        """Update usages of resources."""
        self.real = self.initial.copy()
        self.unassigned = self.initial.copy()
        for task in tasks:
            if task.assignment == self:
                self.real.substract(task.real)
                self.unassigned.substract(task.initial)


@dataclass
class Simulator:
    tasks: List[Task]
    nodes: List[Node]
    scheduler: Algorithm
    allow_rough_assignment: bool = False

    def __post_init__(self):
        self.time = 0

    def get_task_by_name(self, task_name: str) -> Optional[Task]:
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None

    def get_node_by_name(self, node_name: str) -> Optional[Node]:
        for node in self.nodes:
            if node.name == node_name:
                return node
        return None

    def reset(self):
        self.tasks = []
        self.time = 0

    def update_tasks_usage(self, delta_time):
        """It may be simulated that task usage changed across its lifetime."""
        for task in self.tasks:
            task.update(delta_time)

    def update_tasks_list(self, changes):
        deleted, created = changes
        self.tasks = [task for task in self.tasks if task not in deleted]
        for new in created:
            new.assignment = None
            self.tasks.append(new)

    def update_nodes_state(self):
        for node in self.nodes:
            node.update(self.tasks)

    def validate_assignment(self, task: Task, assignment: Node) -> bool:
        return assignment.validate_assignment(self.tasks, task)

    def perform_assignments(self, assignments: Dict[TaskId, Node]) -> int:
        assigned_count = 0
        for task in self.tasks:
            if task.name in assignments:
                if self.validate_assignment(task, assignments[task.name]) or self.allow_rough_assignment:
                    task.assignment = assignments[task.name]
                    assigned_count += 1
        return assigned_count

    def call_scheduler(self, new_task: Task):
        """To map simulator structure into required by scheduler.Algorithm interace."""

        node_names = [node.name for node in self.nodes]
        pod = {'metadata': {'labels': {'app': new_task.name},
               'name': new_task.name, 'namespace': 'default'}}
        extender_args = ExtenderArgs([], pod, node_names)

        extender_filter_result = self.scheduler.filter(extender_args)
        filtered_nodes = [node for node in extender_args.NodeNames
                          if node not in extender_filter_result.FailedNodes]
        # priorities = self.scheduler.prioritize(extender_args)
        # @TODO take into consideration priorities

        if len(filtered_nodes) == 0:
            return {}
        return {new_task.name: self.get_node_by_name(filtered_nodes[0])}

    def iterate(self, delta_time: int, changes: Tuple[List[Task], List[Task]]) -> int:
        self.time += delta_time
        self.update_tasks_usage(delta_time)
        self.update_tasks_list(changes)

        # Update state after deleting tasks.
        self.update_nodes_state()

        assignments = self.call_scheduler(changes[1][0])
        assigned_count = self.perform_assignments(assignments)

        # Recalculating state after assignments being performed.
        self.update_nodes_state()

        return assigned_count

    def iterate_single_task(self, new_task: Task):
        return self.iterate(delta_time=1, changes=([], [new_task]))
