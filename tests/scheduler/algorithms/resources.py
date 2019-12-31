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


class Resources:
    def __init__(self, cpu, mem, membw):
        self.cpu = cpu
        self.mem = mem
        self.membw = membw

    def __repr__(self):
        return str({'cpu': self.cpu,
                    'mem': float(self.mem)/float(GB),
                    'membw': float(self.membw)/float(GB)})

    def create_empty():
        return Resources(0, 0, 0)

    def substract(self, b):
        self.cpu -= b.cpu
        self.mem -= b.mem
        self.membw -= b.membw

    def __bool__(self):
        return self.cpu >= 0 and self.mem >= 0 and self.membw >= 0

    def copy(self):
        return Resources(self.cpu, self.mem, self.membw)
