from wca.scheduler.simulator_experiments.experiment_1 import single_run

from wca.scheduler.algorithms.ffd_generic import FFDGeneric, FFDGenericAsymmetricMembw
from wca.scheduler.cluster_simulator import Node, Resources, Task
from wca.scheduler.types import ResourceType as rt


def task_creation_fun(identifier):
    r = Resources({rt.CPU: 8, rt.MEM: 10, rt.MEMBW: 10, })
    t = Task('stress_ng_{}'.format(identifier), r)
    return t


def task_creation_fun_aep(identifier):
    r = Resources({rt.CPU: 8, rt.MEM: 10,
                   rt.MEMBW_WRITE: 5, rt.MEMBW_READ: 5})
    t = Task('stress_ng_{}'.format(identifier), r)
    return t


def test_single_run():
    simulator_dimensions = {rt.CPU, rt.MEM, rt.MEMBW}
    nodes = [Node('0', Resources({rt.CPU: 96, rt.MEM: 1000, rt.MEMBW: 50})),
             Node('1', Resources({rt.CPU: 96, rt.MEM: 320, rt.MEMBW: 150}))]
    extra_simulator_args = {"allow_rough_assignment": True,
                            "dimensions": simulator_dimensions}
    scheduler_class = FFDGeneric
    extra_scheduler_kwargs = {"dimensions": {rt.CPU, rt.MEM}}

    simulator = single_run(nodes, task_creation_fun, extra_simulator_args,
                           scheduler_class, extra_scheduler_kwargs)
    assert len(simulator.tasks) == 23
    assert len([node for node in simulator.nodes if node.unassigned.data[rt.MEMBW] < 0]) == 1


def test_single_run_membw_write_read():
    """check code membw write/read specific"""
    simulator_dimensions = {rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}
    nodes = [Node('0', Resources(
        {rt.CPU: 96, rt.MEM: 1000, rt.MEMBW_READ: 40, rt.MEMBW_WRITE: 10})),
             Node('1', Resources({rt.CPU: 96, rt.MEM: 320, rt.MEMBW_READ: 150,
                                  rt.MEMBW_WRITE: 150}))]
    extra_simulator_args = {"allow_rough_assignment": True,
                            "dimensions": simulator_dimensions}
    scheduler_class = FFDGenericAsymmetricMembw
    extra_scheduler_kwargs = {}

    simulator = single_run(nodes, task_creation_fun_aep, extra_simulator_args,
                           scheduler_class, extra_scheduler_kwargs)
    assert len(simulator.tasks) == 13
