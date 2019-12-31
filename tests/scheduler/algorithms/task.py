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
from numpy.random import normal as np_normal
from tests.scheduler.algorithms.resources import Resources

GB = 1000 ** 3
MB = 1000 ** 2


class Task:
    def __init__(self, name, initial, assignment=None):
        self.name = name
        self.initial = initial
        self.assignment = assignment

        self.real = Resources.create_empty()
        self.life_time = 0

    def update(self, delta_time):
        self.life_time += delta_time
        # Here simply just if, life_time > 0 assign all
        self.real = self.initial.copy()

    def create_stressng(i, assignment=None):
        r = Resources(8, 10 * GB, 10 * GB)
        t = Task('stress_ng_{}'.format(i), r)
        return t

    def create_random_stressng(i, assignment=None):
        def normal_random(loc, scale):
            r = int(np_normal(loc, scale))
            return r if r >= 1 else 1

        r = Resources(normal_random(8, 5),
                      normal_random(10, 8) * GB,
                      normal_random(10, 8) * GB)
        t = Task('stress_ng_{}'.format(i), r)
        return t

    def create_deterministic_stressng(i):
        pass

    def __repr__(self):
        return "(name: {}, assignment: {}, initial: {}, real: {})".format(
                self.name, 'None' if self.assignment is None else self.assignment.name,
                str(self.initial), str(self.real))
