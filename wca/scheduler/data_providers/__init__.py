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
from abc import ABC, abstractmethod
from typing import Dict, List, Iterable

from wca.scheduler.types import ResourceType, NodeName, Resources, TaskName


class DataProvider(ABC):
    @abstractmethod
    def get_nodes_capacities(self, resources: Iterable[ResourceType]) -> Dict[NodeName, Resources]:
        """Returns for >>nodes<< maximal capacities for >>resources<<"""
        pass

    @abstractmethod
    def get_assigned_tasks_requested_resources(
            self, resources: Iterable[ResourceType], nodes: Iterable[NodeName]) -> Dict[NodeName, Dict[TaskName, Resources]]:
        """Return for all >>nodes<< all tasks requested >>resources<< assigned to them."""
        pass

    def get_app_requested_resources(self, resources: Iterable[ResourceType], app: str) -> Resources:
        """Returns for >>app<< requested resources; if a dimension cannot be read from kubernetes metadata,
           use some kind of approximation for maximal value needed for a dimension."""

    def get_node_membw_read_write_ratio(self, node: str) -> float:
        """For DRAM only node should return 1."""
        pass
