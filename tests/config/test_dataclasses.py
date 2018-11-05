# Copyright (c) 2018 Intel Corporation
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


from typing import List
from dataclasses import dataclass, field

import pytest

from owca import config
from owca import testing


@config.register
@dataclass
class DCExample:
    x: int
    y: str = 'bleblo'
    z: List[int] = field(default_factory=lambda: [1, 2, 3])


def test_dataclass():
    test_config_path = testing.relative_module_path(__file__, 'test_dataclasses.yaml')
    data = config.load_config(test_config_path)

    dc1 = data['dc1']
    assert dc1.x == 5
    assert dc1.y == 'bleblo'
    assert dc1.z == [1, 2, 3]

    dc2 = data['dc2']
    assert dc2.x == 1
    assert dc2.y == 'newble'
    assert dc2.z == [3, 4, 5]


def test_invalid_dataclass():
    test_config_path = testing.relative_module_path(__file__, 'test_dataclasses_invalid.yaml')

    with pytest.raises(config.ConfigLoadError) as e:
        config.load_config(test_config_path)
        assert 'has imporper type' in str(e)

    message = e.value.args[0]
    assert "has improper type" in message
