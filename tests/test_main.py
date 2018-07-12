from unittest import mock
from rmi import main
from rmi.mesos import MesosTask


yaml_config = '''
runner: !DetectionRunner
  node: !MesosNode
  action_delay: 1.
  storage: !LogStorage
  detector: !NOPAnomalyDectector
'''

mesos_tasks_mocks = [
    MesosTask(
        name='test foo task',
        executor_pid=666,
        container_id='uniq_container_id',
        task_id='mesos_like_task_id',
        agent_id='some_mesos_agent_id',
        executor_id='some_mesos_executor_id',
        cgroup_path='/mesos/xxxx-yyy',
    )
]

@mock.patch('sys.argv', ['rmi', '-c', 'configs/no_existing_file.yaml', '-l', 'trace'])
@mock.patch('os.rmdir')
@mock.patch('rmi.config.open', mock.mock_open(read_data=yaml_config))
@mock.patch('rmi.mesos.MesosNode.get_tasks', return_value=mesos_tasks_mocks)
@mock.patch('rmi.resctrl.ResGroup.sync')
@mock.patch('rmi.runner.DetectionRunner.wait_or_finish', return_value=False)
def test_main(os_rmdir_mock, get_tasks_mock, resgroup_sync_mock, runner_wait_or_finish):
    main.main()
