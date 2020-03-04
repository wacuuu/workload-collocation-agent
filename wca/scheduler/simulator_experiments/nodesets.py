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
from wca.scheduler.types import ResourceType as rt

NODES_DEFINITIONS_2TYPES = dict(
    aep={rt.CPU: 40, rt.MEM: 1000, rt.MEMBW: 40, rt.MEMBW_READ: 40, rt.MEMBW_WRITE: 10},
    dram={rt.CPU: 80, rt.MEM: 192, rt.MEMBW: 200, rt.MEMBW_READ: 150, rt.MEMBW_WRITE: 150},
)

NODES_DEFINITIONS_3TYPES = dict(
    aep={rt.CPU: 40, rt.MEM: 1000, rt.MEMBW: 40,
         rt.MEMBW_READ: 40, rt.MEMBW_WRITE: 10, rt.WSS: 256},
    sml={rt.CPU: 48, rt.MEM: 192, rt.MEMBW: 200,
         rt.MEMBW_READ: 150, rt.MEMBW_WRITE: 150, rt.WSS: 192},
    big={rt.CPU: 40, rt.MEM: 394, rt.MEMBW: 200,
         rt.MEMBW_READ: 200, rt.MEMBW_WRITE: 200, rt.WSS: 394}
)

NODES_DEFINITIONS_ARTIFICIAL_2DIM_2TYPES = dict(
    cpuhost={rt.CPU: 100, rt.MEM: 200, rt.MEMBW_READ: 100, rt.MEMBW_WRITE: 100},
    memhost={rt.CPU: 50, rt.MEM: 1000, rt.MEMBW_READ: 100, rt.MEMBW_WRITE: 100},
)
