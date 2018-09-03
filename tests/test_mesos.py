import json
import os

from owca.mesos import MesosNode
from unittest.mock import patch, Mock


@patch('requests.post', return_value=Mock(
    json=Mock(
        return_value=json.load(
            open(os.path.dirname(os.path.abspath(__file__)) +
                 '/fixtures/missing_executor_pid_in_mesos_response.json')),
        status_code=200)))
def test_missing_executor_pid(post):
    node = MesosNode()
    tasks = node.get_tasks()

    assert len(tasks) == 0
