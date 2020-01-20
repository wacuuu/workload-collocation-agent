import pytest
from pprint import pprint

from wca.scheduler.algorithms.ffd_generic import FFDGeneric
from wca.scheduler.cluster_simulator import ClusterSimulator, Node, Resources, GB, Task
from wca.scheduler.data_providers.cluster_simulator_data_provider import (
        ClusterSimulatorDataProvider)
from wca.scheduler.types import ResourceType


# def create_random_stressng(i, assignment=None):
#     def normal_random(loc, scale):
#         r = int(np_normal(loc, scale))
#         return r if r >= 1 else 1
#
#     r = Resources(normal_random(8,5),
#                   normal_random(10, 8) * GB,
#                   normal_random(10, 8) * GB)
#     t = Task('stress_ng_{}'.format(i), r)
#     return t


def prepare_NxM_nodes(apache_pass_count, dram_only_count):
    apache_pass = {ResourceType.CPU: 96, ResourceType.MEM: 1000, ResourceType.MEMBW: 50}
    dram_only = {ResourceType.CPU: 96, ResourceType.MEM: 320, ResourceType.MEMBW: 150}

    inode = 0
    nodes = []
    for i in range(apache_pass_count):
        node = Node(str(inode), available_resources=Resources(apache_pass))
        nodes.append(node)
        inode += 1
    for i in range(dram_only_count):
        node = Node(str(inode), available_resources=Resources(dram_only))
        nodes.append(node)
        inode += 1
    return nodes


def single_run(nodes, tasks_for_iterations, extra_simulator_args, scheduler_class, extra_scheduler_kwargs):
    """Compare standard algorithm with the algorithm which looks also at MEMBW"""
    pprint(locals())
    tasks = []

    simulator=ClusterSimulator(
        tasks=[],
        nodes=nodes,
        scheduler=None,
        **extra_simulator_args)        
    data_proxy = ClusterSimulatorDataProvider(simulator)
    simulator.scheduler = scheduler_class(data_provider=data_proxy, **extra_scheduler_kwargs)

    all_assigned_count = 0
    assigned_count = -1
    iteration = 0

    while assigned_count != 0:
        assigned_count = simulator.iterate_single_task(tasks_for_iterations[iteration])
        all_assigned_count += assigned_count
        iteration += 1

    return (simulator.nodes, simulator.tasks,)


def test_perform_experiment():
    simulator_dimensions = set([ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW,])
    nodes = prepare_NxM_nodes(1, 1)
    def create_task(identifier):
        r = Resources({ResourceType.CPU: 8, ResourceType.MEM: 10, ResourceType.MEMBW: 10})
        t = Task('stress_ng_{}'.format(identifier), r)
        return t
    tasks_for_iterations = [
        create_task(iteration) for iteration in range(30)
    ]
    extra_simulator_args = {"allow_rough_assignment": True,
                            "dimensions": simulator_dimensions}
    scheduler_class = FFDGeneric
    extra_scheduler_kwargs = {"dimensions": set([ResourceType.CPU, ResourceType.MEM])}

    nodes, tasks = single_run(nodes, tasks_for_iterations, extra_simulator_args, scheduler_class, extra_scheduler_kwargs)
    assert len(tasks) == 23
    assert len([node for node in nodes if node.unassigned.data[ResourceType.MEMBW] < 0]) == 1

if __name__ == "__main__":
    perform__nodes_membw_contended()
