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

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from wca.config import assure_type

# Kubernetes
NodeName = str
TaskName = str
AppName = str
FailureMessage = str

#  https://github.com/kubernetes/kubernetes/blob/release-1.15/pkg/scheduler/api/types.go#L299
@dataclass
class ExtenderFilterResult():
    Nodes: List[Dict] = None
    NodeNames: List[NodeName] = field(default_factory=lambda: [])
    FailedNodes: Dict[NodeName, FailureMessage] = field(default_factory=lambda: {})
    Error: str = ''


#  https://github.com/kubernetes/kubernetes/blob/release-1.15/pkg/scheduler/api/types.go#L331
@dataclass
class HostPriority():
    Host: str
    Score: int

    def __repr__(self):
        return '%s=%s' % (self.Host, self.Score)


#  https://github.com/kubernetes/kubernetes/blob/release-1.15/pkg/scheduler/api/types.go#L284
@dataclass
class ExtenderArgs:
    Nodes: Optional[List[Dict]]
    Pod: Optional[Dict]
    NodeNames: List[NodeName]

    def __post_init__(self):

        if self.Nodes:
            assure_type(self.Nodes, List[dict])

        if self.Pod:
            assure_type(self.Pod, dict)

        assure_type(self.NodeNames, List[str])


# Internal
class ResourceType(str, Enum):
    MEM = 'mem'
    CPU = 'cpu'
    MEMBW = 'membw'
    MEMBW_FLAT = 'membw_flat'
    MEMBW_WRITE = 'membw_write'
    MEMBW_READ = 'membw_read'
    WSS = 'wss'

    def __repr__(self):
        return self.value


AppsCount = Dict[AppName, int]
Resources = Dict[ResourceType, float]
