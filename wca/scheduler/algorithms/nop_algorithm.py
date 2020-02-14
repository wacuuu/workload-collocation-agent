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
from typing import Tuple, Any

from wca.scheduler.algorithms import Algorithm, BaseAlgorithm
from wca.scheduler.utils import extract_common_input
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority, NodeName


class NOPAlgorithm(BaseAlgorithm):
    """rst
    NOP algorithm.
    """
    def __init__(self, data_provider):
        super().__init__(self, data_provider)

    def app_fit_node(self, node_name: NodeName, app_name: str,
                     data_provider_queried: Tuple[Any]) -> bool:
        return True

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple[Any]) -> int:
        return 0

    def filter(self, extender_args: ExtenderArgs):
        _, nodes, _, _ = extract_common_input(extender_args)

        return ExtenderFilterResult(Nodes=nodes)

    def prioritize(self, extender_args: ExtenderArgs):
        _, nodes, _, _ = extract_common_input(extender_args)

        return [HostPriority(node, 0) for node in nodes]
