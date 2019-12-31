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
from tests.scheduler.algorithms.resources import Resources

GB = 1000 ** 3
MB = 1000 ** 2


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
        self.real = self.initial.copy()
        self.unassigned = self.initial.copy()
        for task in tasks:
            if task.assignment == self:
                self.real.substract(task.real)
                self.unassigned.substract(task.initial)

    def create_apache_pass():
        return Node('0', Resources(96, 1000 * GB, 50 * GB))

    def create_standard():
        return Node('1', Resources(96, 150 * GB, 150 * GB))
