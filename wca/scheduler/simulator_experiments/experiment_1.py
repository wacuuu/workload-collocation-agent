import datetime
import itertools
from collections import Counter
from pprint import pprint
from typing import Dict, List, Any, Callable

import random
from dataclasses import dataclass

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.algorithms.ffd_generic import FFDGeneric
from wca.scheduler.cluster_simulator import ClusterSimulator, Node, Resources, Task
from wca.scheduler.data_providers.cluster_simulator_data_provider import (
    ClusterSimulatorDataProvider)
from wca.scheduler.types import ResourceType


def single_run(nodes: List[Node], task_creation_fun: Callable[[int], Task],
               extra_simulator_args: Dict, scheduler_class: Algorithm,
               extra_scheduler_kwargs: Dict, iteration_finished_callback: Callable = None):
    """Compare standard algorithm with the algorithm which looks also at MEMBW"""
    pprint(locals())
    tasks = []

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
        random_idx = random.randint(0, len(taskset) - 1)
        task = taskset[random_idx].copy()
        task.name += "___" + str(i)
        r.append(task)
    return r


def randonly_choose_from_taskset_single(taskset, dimensions, name_sufix):
    random_idx = random.randint(0, len(taskset) - 1)
    task = taskset[random_idx].copy()
    task.name += "___" + str(name_sufix)

    task_dim = set(task.requested.data.keys())
    dim_to_remove = task_dim.difference(dimensions)
    for dim in dim_to_remove:
        task.remove_dimension(dim)

    return task


def prepare_NxMxK_nodes__demo_configuration(apache_pass_count, dram_only_v1_count, dram_only_v2_count, dimensions):
    """Taken from WCA team real cluster."""
    apache_pass = {ResourceType.CPU: 80, ResourceType.MEM: 1000, ResourceType.MEMBW: 40, ResourceType.WSS: 256}
    dram_only_v1 = {ResourceType.CPU: 96, ResourceType.MEM: 192, ResourceType.MEMBW: 150, ResourceType.WSS: 192}
    dram_only_v2 = {ResourceType.CPU: 80, ResourceType.MEM: 394, ResourceType.MEMBW: 200, ResourceType.WSS: 394}
    nodes_spec = [apache_pass, dram_only_v1, dram_only_v2]

    # Filter only dimensions required.
    for i, node_spec in enumerate(nodes_spec):
        nodes_spec[i] = {dim: val for dim, val in node_spec.items() if dim in dimensions}

    inode = 0
    nodes = []
    for i_node_type, node_type_count in enumerate((apache_pass_count, dram_only_v1_count, dram_only_v2_count,)):
        for i in range(node_type_count):
            node = Node(str(inode), available_resources=Resources(nodes_spec[i_node_type]))
            nodes.append(node)
            inode += 1
    return nodes


@dataclass
class IterationData:
    cluster_resource_usage: Resources
    per_node_resource_usage: Dict[Node, Resources]
    broken_assignments: Dict[Node, int]
    tasks_types_count: Dict[str, int]


def wrapper_iteration_finished_callback(iterations_data: List[IterationData]):
    def iteration_finished_callback(iteration: int, simulator: ClusterSimulator):
        per_node_resource_usage = simulator.per_node_resource_usage(True)
        cluster_resource_usage = simulator.cluster_resource_usage(True)
        broken_assignments = simulator.rough_assignments_per_node.copy()
        tasks_types_count = Counter([task.get_core_name() for task in simulator.tasks])

        iterations_data.append(IterationData(
            cluster_resource_usage, per_node_resource_usage,
            broken_assignments, tasks_types_count))

    return iteration_finished_callback


def create_report(title: str, header: Dict[str, Any], iterations_data: List[IterationData]):
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
    axs[0].set_title(str(header))
    # ---
    axs[0].set_xlim(iterations.min() - 1, iterations.max() + 1)
    axs[0].set_ylim(0, 1)

    broken_assignments = np.array([sum(list(iter_.broken_assignments.values())) for iter_ in iterd])
    axs[1].plot(iterations, broken_assignments, 'g--')
    axs[1].legend(['broken assignments'])
    axs[1].set_xlabel('iteration')
    axs[1].set_ylabel('')
    axs[1].set_xlim(iterations.min() - 1, iterations.max() + 1)
    axs[1].set_ylim(broken_assignments.min() - 1, broken_assignments.max() + 1)

    t_ = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M')
    fig.savefig('experiments_results/{}__{}.png'.format(title.replace(' ', '_'), t_))

    print(len(iterations_data))
    print(iterations_data[-1].tasks_types_count)


def experiment__nodes_membw_contended():
    # looping around this:
    nodes__ = (
        (3, 4, 2),
        (5, 15, 10),
    )
    scheduler_dimensions__ = (
        ([ResourceType.CPU, ResourceType.MEM, ]),
        ([ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW]),
    )

    for ir, run_params in enumerate(itertools.product(nodes__, scheduler_dimensions__)):
        # reset seed
        random.seed(300)

        simulator_dimensions = {ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW}

        # instead of 3 should be 2, but then results are less visible
        nodes = prepare_NxMxK_nodes__demo_configuration(
            apache_pass_count=run_params[0][0], dram_only_v1_count=run_params[0][1],
            dram_only_v2_count=run_params[0][2],
            dimensions=simulator_dimensions)

        extra_simulator_args = {"allow_rough_assignment": True, "dimensions": simulator_dimensions}
        scheduler_class = FFDGeneric
        extra_scheduler_kwargs = {"dimensions": set(run_params[1])}

        def task_creation_fun(index):
            return randonly_choose_from_taskset_single(tasks__2lm_contention_demo,
                                                       simulator_dimensions, index)

        iterations_data: List[IterationData] = []
        simulator = single_run(nodes, task_creation_fun,
                               extra_simulator_args, scheduler_class, extra_scheduler_kwargs,
                               wrapper_iteration_finished_callback(iterations_data))

        header = {'nodes': run_params[0], 'scheduler_dimensions': run_params[1]}
        create_report('experiment membw contention {}'.format(ir), header, iterations_data)


if __name__ == "__main__":
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        # No installed packages required for report generation.
        exit(1)
    experiment__nodes_membw_contended()
