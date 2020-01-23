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
from typing import Dict, List

from wca.config import assure_type

# Kubernetes
NodeName = str
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
    Nodes: List[Dict]
    Pod: Dict[str, str]
    NodeNames: List[str]

    def __post_init__(self):
        assure_type(self.Nodes, List[Dict])
        assure_type(self.Pod, Dict[str, str])
        assure_type(self.NodeNames, List[str])


# Internal
class ResourceType(Enum):
    MEM = 'mem'
    CPU = 'cpu'
    MEMORY_BANDWIDTH_READS = 'memory_bandwidth_reads'
    MEMORY_BANDWIDTH_WRITES = 'memory_bandwidth_writes'
