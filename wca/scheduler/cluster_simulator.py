from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs, ResourceType

GB = 1000 ** 3
MB = 1000 ** 2

TaskId = str
NodeId = int
Assignments = Dict[TaskId, NodeId]


class Resources:
    def __init__(self, resources):
        self.data = resources

    @staticmethod
    def create_empty(dimensions):
        return Resources({d: 0 for d in dimensions})

    def __repr__(self):
        return str(self.data)

    def __bool__(self):
        return all([val > 0 for val in self.data.values()])

    def __sub__(self, other):
        me = self.copy()
        me.substract(other)
        return me

    def __add__(self, other):
        me = self.copy()
        me.add(other)
        return me

    def __truediv__(self, other):
        me = self.copy()
        me.divide(other)
        return me

    def substract(self, b):
        assert set(self.data.keys()) == set(b.data.keys())
        for key in self.data.keys():
            self.data[key] -= b.data[key]

    def add(self, b):
        assert set(self.data.keys()) == set(b.data.keys())
        for key in self.data.keys():
            self.data[key] += b.data[key]

    @staticmethod
    def sum(array):
        r = Resources.create_empty(list(array[0].data.keys()))
        for el in array:
            r = r + el
        return r

    def divide(self, b):
        assert set(self.data.keys()) == set(b.data.keys())
        for key in self.data.keys():
            self.data[key] /= b.data[key]

    def copy(self):
        r = Resources({})
        r.data = self.data.copy()
        return r


class Task:
    def __init__(self, name, requested, assignment=None):
        self.name: str = name
        self.assignment: Node = assignment
        self.requested: Resource = requested  # == requested
        self.real: Resource = Resources.create_empty(requested.data.keys())
        self.life_time: int = 0

    def remove_dimension(self, resource_type: ResourceType):
        """post creation removal of one of dimension"""
        for resources_ in (self.requested, self.real):
            del resources_.data[resource_type]

    CORE_NAME_SEP = '___'

    def get_core_name(self):
        if self.CORE_NAME_SEP in self.name:
            return self.name[:self.name.find(self.CORE_NAME_SEP)]
        return self.name

    def update(self, delta_time):
        """Update state of task when it becomes older by delta_time."""
        self.life_time += delta_time
        # Here simply just if, life_time > 0 assign all.
        self.real = self.requested.copy()

    def __repr__(self):
        return "(name: {}, assignment: {}, requested: {}, real: {})".format(
            self.name, 'None' if self.assignment is None else self.assignment.name,
            str(self.requested), str(self.real))

    def copy(self):
        return Task(self.name, self.requested.copy(), None)


class Node:
    def __init__(self, name, available_resources):
        self.name = name
        self.initial = available_resources
        self.real = available_resources.copy()
        self.unassigned = available_resources.copy()
        # initial - all available
        # real - free real memory
        # unassigned - free/unassigned memory

    def __repr__(self):
        return "(name: {}, initial: {}, real: {}, unassigned: {})".format(
            self.name, str(self.initial), str(self.real), str(self.unassigned))

    def validate_assignment(self, tasks, new_task):
        """if unassigned > free_not_unassigned"""
        tmp_unassigned = self.initial.copy()
        for task in tasks:
            if task.assignment == self:
                tmp_unassigned.substract(task.requested)
        tmp_unassigned.substract(new_task.requested)
        return bool(tmp_unassigned)

    def update(self, tasks):
        """Update usages of resources."""
        self.real = self.initial.copy()
        self.unassigned = self.initial.copy()
        for task in tasks:
            if task.assignment == self:
                self.real.substract(task.real)
                self.unassigned.substract(task.requested)


@dataclass
class ClusterSimulator:
    tasks: List[Task]
    nodes: List[Node]
    scheduler: Algorithm
    allow_rough_assignment: bool = False
    dimensions: Set[ResourceType] = (ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW,)

    def __post_init__(self):
        self.time = 0
        all([set(node.initial.data.keys()) == self.dimensions for node in self.nodes])
        all([set(task.requested.data.keys()) == self.dimensions for task in self.tasks])
        self.rough_assignments_per_node: Dict[Node, int] = {node:0 for node in self.nodes}

    def get_task_by_name(self, task_name: str) -> Optional[Task]:
        filtered = [task for task in self.tasks if task.name == task_name]
        return filtered[0] if filtered else None

    def get_node_by_name(self, node_name: str) -> Optional[Node]:
        filtered = [node for node in self.nodes if node.name == node_name]
        return filtered[0] if filtered else None

    def per_node_resource_usage(self, if_percentage: bool = False):
        """if_percentage: if output in percentage or original resource units"""
        if if_percentage:
            return [(node.initial - node.unassigned)/node.initial for node in self.nodes]
        return [node.initial - node.unassigned for node in nodes]

    def cluster_resource_usage(self, if_percentage: bool = False):
        r = Resources.sum([node.initial for node in self.nodes]) - Resources.sum([node.unassigned for node in self.nodes])
        if if_percentage:
            r = r / Resources.sum([node.initial for node in self.nodes])
        return r

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
                # taking all dimensions supported by Simulator whether the app fit the node.
                print("Trying to assign task {}".format(task))
                if_app_fit_to_node = self.validate_assignment(task, assignments[task.name])
                if if_app_fit_to_node or self.allow_rough_assignment:
                    task.assignment = assignments[task.name]
                    assigned_count += 1
                    if not if_app_fit_to_node:
                        self.rough_assignments_per_node[task.assignment] += 1
        return assigned_count

    def call_scheduler(self, new_task: Task):
        """To map simulator structure into required by scheduler.Algorithm interace."""

        assert self.dimensions.issubset(set(new_task.requested.data.keys())), \
                '{} {}'.format(set(new_task.requested.data.keys()), self.dimensions)

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
        print("Changes:")
        print(changes)
        print("Assignments performed:")
        print(assignments)
        print('')
        assigned_count = self.perform_assignments(assignments)

        # Recalculating state after assignments being performed.
        self.update_nodes_state()

        return assigned_count

    def iterate_single_task(self, new_task: Task):
        return self.iterate(delta_time=1, changes=([], [new_task]))
