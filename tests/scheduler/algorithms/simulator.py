# Copyright (c) 2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Dict, List, Tuple
from pprint import pprint

from wca.scheduler.types import ExtenderArgs

from tests.scheduler.algorithms.node import Node
from tests.scheduler.algorithms.task import Task

TaskId = str
NodeId = int
Assignments = Dict[TaskId, NodeId]


class Simulator:
    def __init__(self, tasks, nodes, algorithm):
        self.tasks = tasks
        self.nodes = nodes
        self.algorithm = algorithm
        self.time = 0

    def reset(self):
        self.tasks = []
        self.time = 0

    def update_tasks_usage(self, delta_time):
        for task in self.tasks:
            task.update(delta_time)

    def update_tasks_list(self, changes):
        deleted, created = changes
        self.tasks = [task for task in self.tasks if task not in deleted]
        for new in created:
            new.assignment = None
            self.tasks.append(new)

    def calculate_new_state(self):
        for node in self.nodes:
            node.update(self.tasks)

    def validate_assignment(self, task: Task, assignment: Node) -> bool:
        return assignment.validate_assignment(self.tasks, task)

    def perform_assignments(self, assignments: Dict[TaskId, Node]) -> int:
        assigned_count = 0
        for task in self.tasks:
            if task.name in assignments:
                if self.validate_assignment(task, assignments[task.name]):
                    task.assignment = assignments[task.name]
                    assigned_count += 1
        return assigned_count

    def iterate(self, delta_time: int, changes: Tuple[List[Task], List[Task]]) -> int:
        self.time += delta_time
        self.update_tasks_usage(delta_time)
        self.update_tasks_list(changes)

        # Update state after deleting tasks.
        self.calculate_new_state()

        assignments = self.scheduler.schedule(
                self.nodes, [task for task in self.tasks if task.assignment is None])
        pprint("Assignments: {}".format(
            {task_name: node.name for task_name, node in assignments.items()}))
        assigned_count = self.perform_assignments(assignments)

        # Recalculating state after assignments being performed.
        self.calculate_new_state()

        return assigned_count

    def prepare_extender_args(self, pod) -> ExtenderArgs:
        return ExtenderArgs(
                    Nodes={},
                    Pod=pod,
                    NodeNames={
                            [node for node in self.nodes]
                        }
                    )

    def schedule_pod(self, pod):
        extender_args = self.prepare_extender_args(pod)

        extender_filter_result = self.algorithm.filter(extender_args)
        host_priority = self.algorithm.prioritize(extender_args)

        self._schedule(extender_filter_result, host_priority)

    def _schedule(self, extender_filter_result, host_priority):
        pass
