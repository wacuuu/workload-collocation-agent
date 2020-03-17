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
from dataclasses import dataclass

from wca.scheduler.data_providers.cluster_data_provider import ClusterDataProvider
from wca.scheduler.data_providers.creatone import CreatoneDataProvider, AppsProfile, NodeType


@dataclass
class ClusterCreatoneDataProvider(ClusterDataProvider, CreatoneDataProvider):
    app_profiles_query = 'app_profile'
    node_type_query = 'node_type{nodename=%r}'

    def get_apps_profile(self) -> AppsProfile:
        query_result = self.prometheus.do_query(self.app_profiles_query, use_time=True)

        return {row['metric']['app']: float(row['value'][1])
                for row in query_result}

    def get_node_type(self, node) -> NodeType:
        query = self.node_type_query % node
        query_result = self.prometheus.do_query(query, use_time=True)

        node_type = query_result[0]['metric']['nodetype']

        if node_type == NodeType.DRAM:
            return NodeType.DRAM
        elif node_type == NodeType.PMEM:
            return NodeType.PMEM
