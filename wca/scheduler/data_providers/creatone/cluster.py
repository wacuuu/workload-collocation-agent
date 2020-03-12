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
from typing import Dict

from wca.scheduler.data_providers.cluster_data_provider import ClusterDataProvider
from wca.scheduler.data_providers.creatone import CreatoneDataProvider, NodeType

from wca.scheduler.types import AppName, NodeName


@dataclass
class ClusterCreatoneDataProvider(ClusterDataProvider, CreatoneDataProvider):
    app_profiles_query = 'sort_desc(profile_app_2lm_score_max)'
    node_profiles_query = 'node_type'

    def get_app_profiles(self) -> Dict[AppName, float]:
        query_result = self.prometheus.do_query(self.app_profiles_query)

        return {row['metric']['app']: row['value']
                for row in query_result}

    def get_nodes_profiles(self) -> Dict[NodeName, NodeType]:
        query_result = self.prometheus.do_query(self.node_profiles_query)

        return {row['metric']['nodename']: row['metric']['nodetype']
                for row in query_result}
