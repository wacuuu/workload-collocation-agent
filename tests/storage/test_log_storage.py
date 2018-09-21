from unittest.mock import patch, Mock, call

from owca.storage import LogStorage
from owca.metrics import Metric


@patch('owca.storage.get_current_time', return_value=1)
def test_log_storage(*mocks):
    open_mock = Mock()
    with patch('builtins.open', open_mock):
        metric = Metric(name='foo', value=8)
        log_storage = LogStorage(output_filename='mocked_file_name.log')
        log_storage.store([metric])
    assert open_mock.return_value.write.call_count == 2
    assert open_mock.return_value.method_calls[0] == call.write('foo 8 1\n\n')
