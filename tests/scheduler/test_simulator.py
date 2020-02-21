from typing import Dict, List, Callable

from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.algorithms.bar import LeastUsedBar
from wca.scheduler.cluster_simulator import Node, Resources, Task
from wca.scheduler.types import ResourceType as rt

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.cluster_simulator import ClusterSimulator
from wca.scheduler.data_providers.cluster_simulator_data_provider import (
    ClusterSimulatorDataProvider)


def run_until_first_failure(
        nodes: List[Node], task_creation_fun: Callable[[int], Task],
        extra_simulator_args: Dict, scheduler_class: Algorithm,
        extra_scheduler_kwargs: Dict, iteration_finished_callback: Callable = None):
    """Compare standard algorithm with the algorithm which looks also at MEMBW"""
    simulator = ClusterSimulator(
        tasks=[],
        nodes=nodes,
        scheduler=None,
        **extra_simulator_args)
    data_proxy = ClusterSimulatorDataProvider(simulator)
    simulator.scheduler = scheduler_class(data_provider=data_proxy, **extra_scheduler_kwargs)

    iteration = 0
    while simulator.iterate_single_task(task_creation_fun(iteration)) == 1:
        if iteration_finished_callback is not None:
            iteration_finished_callback(iteration, simulator)
        iteration += 1

    return simulator


def task_creation_fun(identifier):
    r = Resources({rt.CPU: 8, rt.MEM: 10})
    t = Task('stress_ng_{}'.format(identifier), r)
    return t


def test_single_run():
    simulator_dimensions = {rt.CPU, rt.MEM}
    nodes = [Node('0', Resources({rt.CPU: 96, rt.MEM: 1000})),
             Node('1', Resources({rt.CPU: 96, rt.MEM: 320}))]
    extra_simulator_args = {"allow_rough_assignment": False,
                            "dimensions": simulator_dimensions}
    scheduler_class = Fit
    extra_scheduler_kwargs = {"dimensions": {rt.CPU, rt.MEM}}

    simulator = run_until_first_failure(
        nodes, task_creation_fun, extra_simulator_args,
        scheduler_class, extra_scheduler_kwargs)
    assert len(simulator.tasks) == 25


def task_creation_fun_aep(identifier):
    r = Resources({rt.CPU: 8, rt.MEM: 10,
                   rt.MEMBW_WRITE: 5, rt.MEMBW_READ: 5})
    t = Task('stress_ng_{}'.format(identifier), r)
    return t


def test_single_run_membw_write_read():
    """check code membw write/read specific"""
    simulator_dimensions = {rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}
    nodes = [Node('0', Resources(
        {rt.CPU: 96, rt.MEM: 1000, rt.MEMBW_READ: 40, rt.MEMBW_WRITE: 10})),
             Node('1', Resources({rt.CPU: 96, rt.MEM: 320, rt.MEMBW_READ: 150,
                                  rt.MEMBW_WRITE: 150}))]
    extra_simulator_args = {"allow_rough_assignment": True,
                            "dimensions": simulator_dimensions}

    extra_scheduler_kwargs = {}
    for scheduler_class, expected_count in ((Fit, 14), (LeastUsedBar, 14)):
        simulator = run_until_first_failure(
            nodes, task_creation_fun_aep, extra_simulator_args,
            scheduler_class, extra_scheduler_kwargs)
        assert len(simulator.tasks) == expected_count
