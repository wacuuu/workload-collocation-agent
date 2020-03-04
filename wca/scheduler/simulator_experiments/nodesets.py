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
from wca.scheduler.types import ResourceType as ResourceType

NODES_DEFINITIONS_2TYPES = dict(
    aep={ResourceType.CPU: 40, ResourceType.MEM: 1000, ResourceType.MEMBW: 40, ResourceType.MEMBW_READ: 40, ResourceType.MEMBW_WRITE: 10},
    dram={ResourceType.CPU: 80, ResourceType.MEM: 192, ResourceType.MEMBW: 200, ResourceType.MEMBW_READ: 150, ResourceType.MEMBW_WRITE: 150},
)

NODES_DEFINITIONS_3TYPES = dict(
    aep={ResourceType.CPU: 40, ResourceType.MEM: 1000, ResourceType.MEMBW: 40,
         ResourceType.MEMBW_READ: 40, ResourceType.MEMBW_WRITE: 10, ResourceType.WSS: 256},
    sml={ResourceType.CPU: 48, ResourceType.MEM: 192, ResourceType.MEMBW: 200,
         ResourceType.MEMBW_READ: 150, ResourceType.MEMBW_WRITE: 150, ResourceType.WSS: 192},
    big={ResourceType.CPU: 40, ResourceType.MEM: 394, ResourceType.MEMBW: 200,
         ResourceType.MEMBW_READ: 200, ResourceType.MEMBW_WRITE: 200, ResourceType.WSS: 394}
)

NODES_DEFINITIONS_ARTIFICIAL_2DIM_2TYPES = dict(
    cpuhost={ResourceType.CPU: 100, ResourceType.MEM: 200, ResourceType.MEMBW_READ: 100, ResourceType.MEMBW_WRITE: 100},
    memhost={ResourceType.CPU: 50, ResourceType.MEM: 1000, ResourceType.MEMBW_READ: 100, ResourceType.MEMBW_WRITE: 100},
)
