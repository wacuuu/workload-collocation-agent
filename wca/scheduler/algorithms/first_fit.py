# Copyright (c) 2019 Intel Corporation
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
from dataclasses import dataclass
from typing import List

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority
from wca.scheduler.utils import extract_common_input


@dataclass
class FirstFit(Algorithm):

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        app, nodes, namespace, name = extract_common_input(extender_args)

        if namespace != self.namespace:
            return ExtenderFilterResult()

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        pass
