from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set
import logging

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs, ResourceType


log = logging.getLogger(__name__)

GB = 1000 ** 3
MB = 1000 ** 2

TaskId = str
NodeId = int
Assignments = Dict[TaskId, NodeId]


class Resources:
    def __init__(self, resources, membw_ratio=1):
        """membw_ratio: ratio of MEMBW_READ / MEMBW_WRITE."""
        self.data = resources

    def __repr__(self):
        return str(self.data)

    @staticmethod
    def create_empty(dimensions):
        return Resources({d: 0 for d in dimensions})

    def copy(self):
        r = Resources({})
        r.data = self.data.copy()
        return r

    def __bool__(self):
        return all([val > 0 for val in self.data.values()])

    def __sub__(self, other):
        me = self.copy()
        me.substract(other)
        return me

    def substract(self, b):
        """simply loops over all dimensions and use - operator"""
        assert set(self.data.keys()) == set(b.data.keys())
        for key in self.data.keys():
            self.data[key] -= b.data[key]

    def substract_aep_aware(self, b, membw_read_write_ratio):
        """Mutates self. """
        assert set(self.data.keys()) == set(b.data.keys())
        for key in self.data.keys():
            if key == ResourceType.MEMBW_READ or key == ResourceType.MEMBW_WRITE:
                continue
            self.data[key] -= b.data[key]

        # Special case for MEMBW
        if ResourceType.MEMBW_READ in self.data and ResourceType.MEMBW_WRITE in self.data:
            READ = ResourceType.MEMBW_READ
            WRITE = ResourceType.MEMBW_WRITE
            x = self.data
            y = b.data
            x[READ] = x[READ] - y[READ] - y[WRITE] * membw_read_write_ratio
            x[WRITE] = x[WRITE] - y[WRITE] - y[READ] / membw_read_write_ratio

    def __add__(self, other):
        me = self.copy()
        me.add(other)
        return me

    def add(self, b):
        """simply loops over all dimensions and use + operator"""
        assert set(self.data.keys()) == set(b.data.keys())
        for key in self.data.keys():
            self.data[key] += b.data[key]

    @staticmethod
    def sum(array):
        r = Resources.create_empty(list(array[0].data.keys()))
        for el in array:
            r = r + el
        return r

    def __truediv__(self, other):
        me = self.copy()
        me.divide(other)
        return me

    def divide(self, b):
        assert set(self.data.keys()) == set(b.data.keys())
        for key in self.data.keys():
            self.data[key] /= b.data[key]


class Task:
    def __init__(self, name, requested, assignment=None):
        self.name: str = name
        self.assignment: Node = assignment
        self.requested: Resources = requested  # == requested
        self.real: Resources = Resources.create_empty(requested.data.keys())
        self.life_time: int = 0

    def remove_dimension(self, resource_type: ResourceType):
        """Post-creation removal of one of the dimensions."""
        for resources_ in (self.requested, self.real):
            del resources_.data[resource_type]

    def add_dimension(self, resource_type: ResourceType, requested_val):
        """Post-creation addition of a dimension."""
        self.requested.data[resource_type] = requested_val
        self.real.data[resource_type] = 0

    CORE_NAME_SEP = '___'

    def get_core_name(self):
        if self.CORE_NAME_SEP in self.name:
            return self.name[:self.name.find(self.CORE_NAME_SEP)]
        return self.name

    def update(self, delta_time):
        """Update state of task when it becomes older by delta_time."""
        self.life_time += delta_time
        # Here simply just if, life_time > 0 assign all requested.
        self.real = self.requested.copy()

    def __repr__(self):
        return "(name: {}, assignment: {}, requested: {}, real: {})".format(
            self.name, 'None' if self.assignment is None else self.assignment.name,
            str(self.requested), str(self.real))

    def copy(self):
        return Task(self.name, self.requested.copy(), None)


class Node:
    def __init__(self, name, available_resources):
        # initial - all available
        # real - free real memory
        # unassigned - free/unassigned memory
        self.name = name
        self.initial = available_resources
        self.free = available_resources.copy()
        self.unassigned = available_resources.copy()

    def __repr__(self):
        return "(name: {}, initial: {}, free: {}, unassigned: {})".format(
            self.name, str(self.initial), str(self.free), str(self.unassigned))

    def get_membw_read_write_ratio(self):
        d_ = self.initial.data
        if ResourceType.MEMBW_READ in d_ and ResourceType.MEMBW_WRITE in d_:
            return d_[ResourceType.MEMBW_READ] / d_[ResourceType.MEMBW_WRITE]
        return 1

    # @staticmethod
    # def substract_resources(a: Resources, b: Resources):
    #     """returns c = a - b"""
    #     assert set(a.data.keys()) == set(b.data.keys())
    #     c = a.copy()
    #     for key in self.data.keys():
    #         if key == ResourceType.MEMBW_READ or key == ResourceType.MEMBW_WRITE:
    #             continue
    #         c.data[key] -= b.data[key]
    #     # Special case for MEMBW
    #     if ResourceType.MEMBW_READ in c.data and ResourceType.MEMBW_WRITE in c.data:
    #         READ = ResourceType.MEMBW_READ
    #         WRITE = ResourceType.MEMBW_WRITE
    #         x = c.data
    #         y = b.data
    #         x[READ] = x[READ] - y[READ] - y[WRITE] * membw_read_write_ratio
    #         x[WRITE] = x[WRITE] - y[WRITE] - y[READ] / membw_read_write_ratio
    #     return c

    def validate_assignment(self, tasks, new_task):
        """Check if there is enough resources on the node for a >>new_task<<."""
        tmp_unassigned: Resources = self.initial.copy()
        for task in tasks:
            if task.assignment == self:
                tmp_unassigned.substract_aep_aware(task.requested,
                                                   self.get_membw_read_write_ratio())
        tmp_unassigned.substract_aep_aware(new_task.requested, self.get_membw_read_write_ratio())
        return bool(tmp_unassigned)

    def update(self, tasks):
        """Update usages of resources (recalculate self.free and self.unassigned)"""
        self.free = self.initial.copy()
        self.unassigned = self.initial.copy()
        for task in tasks:
            if task.assignment == self:
                self.free.substract_aep_aware(task.real, self.get_membw_read_write_ratio())
                self.unassigned.substract_aep_aware(task.requested,
                                                    self.get_membw_read_write_ratio())


@dataclass
class ClusterSimulator:
    tasks: List[Task]
    nodes: List[Node]
    scheduler: Optional[Algorithm]
    allow_rough_assignment: bool = False
    dimensions: Set[ResourceType] = (ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW,)

    def __post_init__(self):
        self.time = 0
        all([set(node.initial.data.keys()) == self.dimensions for node in self.nodes])
        all([set(task.requested.data.keys()) == self.dimensions for task in self.tasks])
        self.rough_assignments_per_node: Dict[Node, int] = {node: 0 for node in self.nodes}

    def get_task_by_name(self, task_name: str) -> Optional[Task]:
        filtered = [task for task in self.tasks if task.name == task_name]
        return filtered[0] if filtered else None

    def get_node_by_name(self, node_name: str) -> Optional[Node]:
        filtered = [node for node in self.nodes if node.name == node_name]
        return filtered[0] if filtered else None

    def per_node_resource_usage(self, if_percentage: bool = False):
        """if_percentage: if output in percentage or original resource units"""
        node_resource_usage = {node: Resources.create_empty(self.dimensions) for node in self.nodes}
        for task in self.tasks:
            if task.assignment is None:
                continue
            node_resource_usage[task.assignment] += task.requested

        if if_percentage:
            return {node: node_resource_usage[node]/node.initial
                    for node in node_resource_usage.keys()}
        return node_resource_usage

    def cluster_resource_usage(self, if_percentage: bool = False):
        node_resource_usage = self.per_node_resource_usage()

        r = Resources.sum([usage for usage in node_resource_usage.values()])
        if if_percentage:
            r = r / Resources.sum([node.initial for node in self.nodes])
        return r

    def reset(self):
        self.tasks = []
        self.time = 0

    def update_tasks_usage(self, delta_time):
        """It may be simulated that task usage changes across its lifetime."""
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
            '{} {}'.format(set(new_task.requested.data.keys()),
                           self.dimensions)

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
        log.debug("--- Iteration start ---")
        self.time += delta_time
        self.update_tasks_usage(delta_time)
        self.update_tasks_list(changes)

        # Update state after deleting tasks.
        self.update_nodes_state()

        assignments = self.call_scheduler(changes[1][0])
        log.debug("Changes: {}".format(changes))
        log.debug("Assignments performed: {}".format(assignments))
        log.debug("Tasks assigned count: {}".format(len([task for task in self.tasks if task.assignment is not None])))
        assigned_count = self.perform_assignments(assignments)

        # Recalculating state after assignments being performed.
        self.update_nodes_state()

        log.debug("--- Iteration ends ---")

        return assigned_count

    def iterate_single_task(self, new_task: Task):
        return self.iterate(delta_time=1, changes=([], [new_task]))
