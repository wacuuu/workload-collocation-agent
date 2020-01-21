from collections import Counter
from dataclasses import dataclass
import pytest
from pprint import pprint
import random
from typing import Dict, List

from wca.scheduler.algorithms.ffd_generic import FFDGeneric
from wca.scheduler.cluster_simulator import ClusterSimulator, Node, Resources, GB, Task
from wca.scheduler.data_providers.cluster_simulator_data_provider import (
        ClusterSimulatorDataProvider)
from wca.scheduler.types import ResourceType


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


def prepare_NxMxK_nodes__demo_configuration(apache_pass_count, dram_only_v1_count, dram_only_v2_count):
    """Taken from wca team real cluster."""
    apache_pass = {ResourceType.CPU: 80, ResourceType.MEM: 1000, ResourceType.MEMBW: 40, ResourceType.WSS: 256}
    dram_only_v1 = {ResourceType.CPU: 96, ResourceType.MEM: 192, ResourceType.MEMBW: 150, ResourceType.WSS: 192}
    dram_only_v2 = {ResourceType.CPU: 80, ResourceType.MEM: 394, ResourceType.MEMBW: 200, ResourceType.WSS: 394}
    nodes_spec = (apache_pass, dram_only_v1, dram_only_v2)

    inode=0
    nodes = [] 
    for i_node_type, node_type_count in enumerate((apache_pass_count, dram_only_v1_count, dram_only_v2_count,)):
        for i in range(node_type_count):
            node = Node(str(inode), available_resources=Resources(nodes_spec[i_node_type]))
            nodes.append(node)
            inode += 1
    return nodes


def single_run(nodes, tasks_for_iterations, extra_simulator_args, scheduler_class, extra_scheduler_kwargs, iteration_finished_callback=None):
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

    iteration = 0
    while iteration < len(tasks_for_iterations) and \
            simulator.iterate_single_task(tasks_for_iterations[iteration]) == 1:
        if iteration_finished_callback is not None:
            iteration_finished_callback(iteration, simulator)
        iteration += 1

    return simulator


# taken from 2lm contention demo slides:
# wca_load_balancing_multidemnsional_2lm_v0.2
tasks__2lm_contention_demo = [
    Task(name='memcached_big', 
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 28,
                              ResourceType.MEMBW: 1.3, ResourceType.WSS: 1.7})),
    Task(name='memcached_medium', 
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 12,
                              ResourceType.MEMBW: 1.0, ResourceType.WSS: 1.0})),
    Task(name='memcached_small', 
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 2.5,
                              ResourceType.MEMBW: 0.4, ResourceType.WSS: 0.4})),
    # ---
    Task(name='redis_big',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 29,
                              ResourceType.MEMBW: 0.5, ResourceType.WSS: 14})),
    Task(name='redis_medium',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 11,
                              ResourceType.MEMBW: 0.4, ResourceType.WSS: 10})),
    Task(name='redis_small',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1.5,
                              ResourceType.MEMBW: 0.3, ResourceType.WSS: 1.5})),
    # ---
    Task(name='stress_stream_big',
         requested=Resources({ResourceType.CPU: 3, ResourceType.MEM: 13,
                              ResourceType.MEMBW: 18, ResourceType.WSS: 12})),
    Task(name='stress_stream_medium',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 12,
                              ResourceType.MEMBW: 6, ResourceType.WSS: 10})),
    Task(name='stress_stream_small',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 7,
                              ResourceType.MEMBW: 5, ResourceType.WSS: 6})),
    # ---
    Task(name='sysbench_big',
         requested=Resources({ResourceType.CPU: 3, ResourceType.MEM: 9,
                              ResourceType.MEMBW: 13, ResourceType.WSS: 7.5})),
    Task(name='sysbench_medium',
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 2,
                              ResourceType.MEMBW: 10, ResourceType.WSS: 2})),
    Task(name='sysbench_small',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1,
                              ResourceType.MEMBW: 8, ResourceType.WSS: 1}))
]


def randonly_choose_from_taskset(taskset, size, seed):
    random.seed(seed)
    r = []
    for i in range(size):
        random_idx = random.randint(0, len(taskset)-1)
        task = taskset[random_idx].copy()
        task.name += "___" + str(i)
        r.append(task)
    return r


def experiment__nodes_membw_contended():
    # instead of 3 should be 2, but then results are less visible
    nodes = prepare_NxMxK_nodes__demo_configuration(apache_pass_count=0, dram_only_v1_count=4, dram_only_v2_count=2)

    simulator_dimensions = set([ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW,])
    extra_simulator_args = {"allow_rough_assignment": True, "dimensions": simulator_dimensions}
    scheduler_class = FFDGeneric
    extra_scheduler_kwargs = {"dimensions": set([ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW])}

    @dataclass
    class IterationData:
        cluster_resource_usage: Resources
        per_node_resource_usage: Dict[Node, Resources]
        broken_assignments: Dict[Node, int]
        tasks_types_count: Dict[str, int]

    iterations_data: List[IterationData] = []
    def iteration_finished_callback(iteration: int, simulator: ClusterSimulator):
        per_node_resource_usage = simulator.per_node_resource_usage(True)
        cluster_resource_usage = simulator.cluster_resource_usage(True)
        broken_assignments = simulator.rough_assignments_per_node.copy()
        tasks_types_count = Counter([task.get_core_name() for task in simulator.tasks])

        iterations_data.append(IterationData(
            cluster_resource_usage, per_node_resource_usage,
            broken_assignments, tasks_types_count))

    tasks_for_iterations = randonly_choose_from_taskset(taskset=tasks__2lm_contention_demo, size=200, seed=300)
    simulator = single_run(nodes, tasks_for_iterations,
                           extra_simulator_args, scheduler_class, extra_scheduler_kwargs,
                           iteration_finished_callback)

    def create_report(title, iterations_data: List[IterationData]):
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            # No installed packages required for report generation.
            return

        plt.style.use('ggplot')
        iterd = iterations_data

        iterations = np.arange(0, len(iterd))
        cpu_usage = np.array([iter_.cluster_resource_usage.data[ResourceType.CPU] for iter_ in iterd])
        mem_usage = np.array([iter_.cluster_resource_usage.data[ResourceType.MEM] for iter_ in iterd])
        membw_usage = np.array([iter_.cluster_resource_usage.data[ResourceType.MEMBW] for iter_ in iterd])
        # ---
        fig, axs = plt.subplots(2)
        axs[0].plot(iterations, cpu_usage, 'r--')
        axs[0].plot(iterations, mem_usage, 'b--')
        axs[0].plot(iterations, membw_usage, 'g--')
        axs[0].legend(['cpu usage', 'mem usage', 'membw usage'])
        # ---
        # axs[0].xlabel('iteration')
        # axs[0].ylabel('')
        axs[0].set_title(title)
        # axs[0].grid(False)
        # ---
        axs[0].set_xlim( iterations.min() - 1, iterations.max() + 1 )
        axs[0].set_ylim(0, 1)

        broken_assignments = np.array([sum(list(iter_.broken_assignments.values())) for iter_ in iterd])
        axs[1].plot(iterations, broken_assignments, 'g--')
        axs[1].legend(['broken assignments'])
        axs[1].set_xlabel('iteration')
        axs[1].set_ylabel('')
        axs[1].set_xlim( iterations.min() - 1, iterations.max() + 1 )
        axs[1].set_ylim( broken_assignments.min()-1, broken_assignments.max()+1)

        fig.savefig('{}.png'.format(title))

    create_report('Summary', iterations_data)
    print(len(iterations_data))
    print(iterations_data[-1].tasks_types_count)


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

    simulator = single_run(nodes, tasks_for_iterations, extra_simulator_args, scheduler_class, extra_scheduler_kwargs)
    assert len(simulator.tasks) == 23
    assert len([node for node in simulator.nodes if node.unassigned.data[ResourceType.MEMBW] < 0]) == 1


if __name__ == "__main__":
    experiment__nodes_membw_contended()
