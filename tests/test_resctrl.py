from unittest.mock import call, MagicMock, patch

from rmi.resctrl import ResGroup, check_resctrl
from rmi.testing import create_open_mock


@patch('builtins.open', new=create_open_mock({
    "/sys/fs/resctrl": "0",
    "/sys/fs/resctrl/mon_data": "0",
}))
def test_check_resctrl(*mock):
    assert check_resctrl()


@patch('rmi.resctrl.log.warning')
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
def test_sync(makedirs_mock, exists_mock, log_warning_mock):
    resctrl_file_mock_simple_name = MagicMock()
    resctrl_file_mock_complex_name = MagicMock()
    open_mock = create_open_mock({
        "/sys/fs/resctrl": "0",
        "/sys/fs/cgroup/cpu/ddd/tasks": "123",
        "/sys/fs/resctrl/ddd/tasks": resctrl_file_mock_simple_name,
        "/sys/fs/cgroup/cpu/ddd/ddd/tasks": "123",
        "/sys/fs/resctrl/ddd-ddd/tasks": resctrl_file_mock_complex_name,
    })
    with patch('builtins.open', open_mock):
        cgroup_path = "/ddd"
        resgroup = ResGroup(cgroup_path)
        resgroup.sync()
        resctrl_file_mock_simple_name.assert_called_once_with('/sys/fs/resctrl/ddd/tasks', 'w')
        resctrl_file_mock_simple_name.assert_has_calls([call().__enter__().write('123')])
    with patch('builtins.open', open_mock):
        cgroup_path = "/ddd/ddd"
        resgroup = ResGroup(cgroup_path)
        resgroup.sync()
        resctrl_file_mock_complex_name.assert_called_once_with('/sys/fs/resctrl/ddd-ddd/tasks', 'w')
        resctrl_file_mock_complex_name.assert_has_calls([call().__enter__().write('123')])


@patch('rmi.resctrl.log.warning')
@patch('os.path.exists', return_value=False)
def test_sync_resctrl_not_mounted(exists_mock, log_warning_mock):
    cgroup_path = "/ddd"
    resgroup = ResGroup(cgroup_path)
    resgroup.sync()
    log_warning_mock.assert_called_once_with('Resctrl not mounted, ignore sync!')


@patch('builtins.open', new=create_open_mock({
    "/sys/fs/resctrl/ddd/mon_data/1/mbm_total_bytes": "1",
    "/sys/fs/resctrl/ddd/mon_data/2/mbm_total_bytes": "1",
    "/sys/fs/cgroup/cpu/ddd/cpuacct.usage": "4",
}))
@patch('os.listdir', return_value=['1', '2'])
def test_get_measurements(*mock):
    cgroup_path = "/ddd"
    resgroup = ResGroup(cgroup_path)
    assert {'memory_bandwidth': 2, 'cpu_usage': 4} == resgroup.get_measurements()
