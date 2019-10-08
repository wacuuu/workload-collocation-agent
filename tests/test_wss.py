from wca.wss import WSS
from tests.testing import create_open_mock
from unittest.mock import Mock, patch


pids = ['1', '2', '3', '4', '5']

smaps = {'/proc/{}/smaps'.format(pid): 'Referenced: {}'.format(pid) for pid in pids}

clear_refs = {'/proc/{}/clear_refs'.format(pid): pid for pid in pids}


@patch('builtins.open', new=create_open_mock({**smaps, **clear_refs}))
@patch('os.listdir', return_value=pids)
def test_get_measurements(*mocks):
    mock_get_pids = Mock()
    mock_get_pids.return_value = ['1', '2', '3', '4', '5']

    wss = WSS(get_pids=mock_get_pids, reset_interval=1)
    assert wss.get_measurements() == {'wss_referenced_mb': 0.0146484375}
