from wca.scheduler.simulator_experiments.experiment_1 import single_run

from wca.scheduler.algorithms.ffd_generic import FFDGeneric, FFDGenericAsymmetricMembw
from wca.scheduler.cluster_simulator import Node, Resources, Task
from wca.scheduler.types import ResourceType


def task_creation_fun(identifier):
    r = Resources({ResourceType.CPU: 8, ResourceType.MEM: 10, ResourceType.MEMBW: 10, })
    t = Task('stress_ng_{}'.format(identifier), r)
    return t


def task_creation_fun_aep(identifier):
    r = Resources({ResourceType.CPU: 8, ResourceType.MEM: 10,
                   ResourceType.MEMBW_WRITE: 5, ResourceType.MEMBW_READ: 5})
    t = Task('stress_ng_{}'.format(identifier), r)
    return t


def test_single_run():
    simulator_dimensions = {ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW}
    nodes = [Node('0', Resources({ResourceType.CPU: 96, ResourceType.MEM: 1000, ResourceType.MEMBW: 50})),
             Node('1', Resources({ResourceType.CPU: 96, ResourceType.MEM: 320, ResourceType.MEMBW: 150}))]
    extra_simulator_args = {"allow_rough_assignment": True,
                            "dimensions": simulator_dimensions}
    scheduler_class = FFDGeneric
    extra_scheduler_kwargs = {"dimensions": {ResourceType.CPU, ResourceType.MEM}}

    simulator = single_run(nodes, task_creation_fun, extra_simulator_args,
                           scheduler_class, extra_scheduler_kwargs)
    assert len(simulator.tasks) == 23
    assert len([node for node in simulator.nodes if node.unassigned.data[ResourceType.MEMBW] < 0]) == 1


def test_single_run_membw_write_read():
    """check code membw write/read specific"""
    simulator_dimensions = {ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW_READ, ResourceType.MEMBW_WRITE}
    nodes = [Node('0', Resources(
        {ResourceType.CPU: 96, ResourceType.MEM: 1000, ResourceType.MEMBW_READ: 40, ResourceType.MEMBW_WRITE: 10})),
             Node('1', Resources({ResourceType.CPU: 96, ResourceType.MEM: 320, ResourceType.MEMBW_READ: 150,
                                  ResourceType.MEMBW_WRITE: 150}))]
    extra_simulator_args = {"allow_rough_assignment": True,
                            "dimensions": simulator_dimensions}
    scheduler_class = FFDGenericAsymmetricMembw
    extra_scheduler_kwargs = {}

    simulator = single_run(nodes, task_creation_fun_aep, extra_simulator_args,
                           scheduler_class, extra_scheduler_kwargs)
    assert len(simulator.tasks) == 13
