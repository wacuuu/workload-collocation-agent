from rmi.cgroups import Cgroup

from unittest.mock import patch, mock_open

from rmi.metrics import MetricName


@patch('builtins.open', mock_open(read_data='100'))
def test_get_measurements():
    cgroup = Cgroup('/some/foo1')
    measurements = cgroup.get_measurements()
    assert measurements == {MetricName.CPU_USAGE_PER_TASK: 100}
