import errno
from unittest.mock import call, MagicMock, patch

import pytest

from owca.resctrl import ResGroup, check_resctrl
from owca.testing import create_open_mock


@patch('builtins.open', new=create_open_mock({
    "/sys/fs/resctrl": "0",
    "/sys/fs/resctrl/tasks": "0",
    "/sys/fs/resctrl/mon_data/mon_L3_00/mbm_total_bytes": "0",
}))
def test_check_resctrl(*mock):
    assert check_resctrl()


@patch('owca.resctrl.log.warning')
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


@patch('owca.resctrl.log.warning')
@patch('os.path.exists', return_value=True)
@patch('os.makedirs', side_effect=OSError(errno.ENOSPC, "mock"))
@patch('builtins.open', new=create_open_mock({
        "/sys/fs/cgroup/cpu/ddd/tasks": "123",
        }))
def test_sync_no_space_left_on_device(makedirs_mock, exists_mock, log_warning_mock):
    resgroup = ResGroup("/ddd")
    with pytest.raises(Exception, match='Limit of workloads reached'):
        resgroup.sync()


@patch('owca.resctrl.log.warning')
@patch('os.path.exists', return_value=False)
def test_sync_resctrl_not_mounted(exists_mock, log_warning_mock):
    cgroup_path = "/ddd"
    resgroup = ResGroup(cgroup_path)
    resgroup.sync()
    log_warning_mock.assert_called_once_with('Resctrl not mounted, ignore sync!')


@patch('builtins.open', new=create_open_mock({
    "/sys/fs/resctrl/ddd/mon_data/1/mbm_total_bytes": "1",
    "/sys/fs/resctrl/ddd/mon_data/2/mbm_total_bytes": "1",
    "/sys/fs/resctrl/ddd/mon_data/1/llc_occupancy": "1",
    "/sys/fs/resctrl/ddd/mon_data/2/llc_occupancy": "1",
    "/sys/fs/cgroup/cpu/ddd/cpuacct.usage": "4",
}))
@patch('os.listdir', return_value=['1', '2'])
def test_get_measurements(*mock):
    cgroup_path = "/ddd"
    resgroup = ResGroup(cgroup_path)
    assert {'memory_bandwidth': 2, 'llc_occupancy': 2} == resgroup.get_measurements()


@patch('builtins.open', new=create_open_mock({
    "/sys/fs/resctrl/mesos-1/tasks": "1\n2\n",
    "/sys/fs/resctrl/mesos-2/tasks": "",  # resctrl group to recycle - expected to be removed.
    "/sys/fs/resctrl/mesos-3/tasks": "2",
}))
@patch('os.listdir', return_value=['mesos-1', 'mesos-2', 'mesos-3'])
@patch('os.rmdir')
@patch('os.path.isdir', return_value=True)
@patch('os.path.exists', return_value=True)
def test_clean_resctrl(exists_mock, isdir_mock, rmdir_mock, listdir_mock):
    from owca.resctrl import cleanup_resctrl
    cleanup_resctrl()
    listdir_mock.assert_called_once()
    assert isdir_mock.call_count == 3
    assert exists_mock.call_count == 3
    rmdir_mock.assert_called_once_with('/sys/fs/resctrl/mesos-2')
