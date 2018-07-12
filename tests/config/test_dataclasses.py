from typing import List
from dataclasses import dataclass, field

import pytest

from rmi import config
from rmi import testing


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

    with pytest.raises(config.ValidationError) as e:
        config.load_config(test_config_path)

    message = e.value.args[0]
    assert "Value 'asdf' for field 'x' in class 'DCExample' " in message
