import datetime
import itertools
from collections import Counter
from pprint import pprint
from typing import Dict, List, Any, Callable

import random
from dataclasses import dataclass

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.algorithms.ffd_generic import FFDGeneric, FFDAsymmetricMembw
from wca.scheduler.cluster_simulator import ClusterSimulator, Node, Resources, Task
from wca.scheduler.data_providers.cluster_simulator_data_provider import (
    ClusterSimulatorDataProvider)
from wca.scheduler.types import ResourceType as rt


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
         requested=Resources({rt.CPU: 2, rt.MEM: 28,
                              rt.MEMBW: 1.3, rt.WSS: 1.7})),
    Task(name='memcached_medium',
         requested=Resources({rt.CPU: 2, rt.MEM: 12,
                              rt.MEMBW: 1.0, rt.WSS: 1.0})),
    Task(name='memcached_small',
         requested=Resources({rt.CPU: 2, rt.MEM: 2.5,
                              rt.MEMBW: 0.4, rt.WSS: 0.4})),
    # ---
    Task(name='redis_big',
         requested=Resources({rt.CPU: 1, rt.MEM: 29,
                              rt.MEMBW: 0.5, rt.WSS: 14})),
    Task(name='redis_medium',
         requested=Resources({rt.CPU: 1, rt.MEM: 11,
                              rt.MEMBW: 0.4, rt.WSS: 10})),
    Task(name='redis_small',
         requested=Resources({rt.CPU: 1, rt.MEM: 1.5,
                              rt.MEMBW: 0.3, rt.WSS: 1.5})),
    # ---
    Task(name='stress_stream_big',
         requested=Resources({rt.CPU: 3, rt.MEM: 13,
                              rt.MEMBW: 18, rt.WSS: 12})),
    Task(name='stress_stream_medium',
         requested=Resources({rt.CPU: 1, rt.MEM: 12,
                              rt.MEMBW: 6, rt.WSS: 10})),
    Task(name='stress_stream_small',
         requested=Resources({rt.CPU: 1, rt.MEM: 7,
                              rt.MEMBW: 5, rt.WSS: 6})),
    # ---
    Task(name='sysbench_big',
         requested=Resources({rt.CPU: 3, rt.MEM: 9,
                              rt.MEMBW: 13, rt.WSS: 7.5})),
    Task(name='sysbench_medium',
         requested=Resources({rt.CPU: 2, rt.MEM: 2,
                              rt.MEMBW: 10, rt.WSS: 2})),
    Task(name='sysbench_small',
         requested=Resources({rt.CPU: 1, rt.MEM: 1,
                              rt.MEMBW: 8, rt.WSS: 1}))
]


def extend_membw_dimensions_to_write_read(taskset):
    """replace dimensions rt.MEMBW with rt.MEMBW_WRITE and rt.MEMBW_READ"""
    new_taskset = []
    for task in taskset:
        task_ = task.copy()
        membw = task_.requested.data[rt.MEMBW]
        task_.remove_dimension(rt.MEMBW)
        task_.add_dimension(rt.MEMBW_READ, membw)
        task_.add_dimension(rt.MEMBW_WRITE, 0)
        new_taskset.append(task_)
    return new_taskset


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


def prepare_NxMxK_nodes__demo_configuration(apache_pass_count, dram_only_v1_count,
                                            dram_only_v2_count, dimensions):
    """Taken from WCA team real cluster."""
    apache_pass = {rt.CPU: 80, rt.MEM: 1000, rt.MEMBW: 40, rt.MEMBW_READ:40,
                   rt.MEMBW_WRITE:10, rt.WSS: 256}
    dram_only_v1 = {rt.CPU: 96, rt.MEM: 192, rt.MEMBW: 150, rt.MEMBW_READ:150,
                    rt.MEMBW_WRITE: 150, rt.WSS: 192}
    dram_only_v2 = {rt.CPU: 80, rt.MEM: 394, rt.MEMBW: 200, rt.MEMBW_READ:200,
                    rt.MEMBW_WRITE:200, rt.WSS: 394}
    nodes_spec = [apache_pass, dram_only_v1, dram_only_v2]

    # Filter only dimensions required.
    for i, node_spec in enumerate(nodes_spec):
        nodes_spec[i] = {dim: val for dim, val in node_spec.items() if dim in dimensions}

    inode = 0
    nodes = []
    for i_node_type, node_type_count in enumerate((apache_pass_count, dram_only_v1_count,
                                                   dram_only_v2_count,)):
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
    cpu_usage = np.array([iter_.cluster_resource_usage.data[rt.CPU] for iter_ in iterd])
    mem_usage = np.array([iter_.cluster_resource_usage.data[rt.MEM] for iter_ in iterd])

    if rt.MEMBW_READ in iterd[0].cluster_resource_usage.data:
        membw_usage = np.array([iter_.cluster_resource_usage.data[rt.MEMBW_READ] for iter_ in iterd])
    else:
        membw_usage = np.array([iter_.cluster_resource_usage.data[rt.MEMBW] for iter_ in iterd])
    # ---
    fig, axs = plt.subplots(2)
    fig.set_size_inches(11,11)
    axs[0].plot(iterations, cpu_usage, 'r--')
    axs[0].plot(iterations, mem_usage, 'b--')
    axs[0].plot(iterations, membw_usage, 'g--')
    axs[0].legend(['cpu usage', 'mem usage', 'membw usage'])
    # ---
    axs[0].set_title(str(header), fontsize=10)
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

    print("Iterations: {}".format(len(iterations_data)))
    print("Assigned tasks: {}".format(iterations_data[-1].tasks_types_count))
    print("Broken assignments: {}".format(sum(iterations_data[-1].broken_assignments.values())))


def experiment__nodes_membw_contended():
    # looping around this:
    nodes__ = (
        (3, 4, 2),
        (5, 15, 10),
    )
    scheduler_dimensions__ = (
        ([rt.CPU, rt.MEM, ]),
        ([rt.CPU, rt.MEM, rt.MEMBW]),
    )

    for ir, run_params in enumerate(itertools.product(nodes__, scheduler_dimensions__)):
        # reset seed
        random.seed(300)

        simulator_dimensions = {rt.CPU, rt.MEM, rt.MEMBW}

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
        single_run(nodes, task_creation_fun,
                   extra_simulator_args, scheduler_class, extra_scheduler_kwargs,
                   wrapper_iteration_finished_callback(iterations_data))

        header = {'nodes': run_params[0], 'scheduler_dimensions': run_params[1]}
        create_report('experiment membw contention {}'.format(ir), header, iterations_data)


def experiment__ffdassymetricmembw__tco():
    # looping around this:
    nodes__ = (
        (3, 4, 2),
        (5, 15, 10),
    )
    scheduler_dimensions__ = (
        ([rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE]),
    )

    for ir, run_params in enumerate(itertools.product(nodes__, scheduler_dimensions__)):
        # reset seed
        random.seed(300)

        simulator_dimensions = {rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}

        # Instead of 3 should be 2, but then results are less visible.
        nodes = prepare_NxMxK_nodes__demo_configuration(
            apache_pass_count=run_params[0][0], dram_only_v1_count=run_params[0][1],
            dram_only_v2_count=run_params[0][2],
            dimensions=simulator_dimensions)

        extra_simulator_args = {"allow_rough_assignment": True, "dimensions": simulator_dimensions}
        scheduler_class = FFDAsymmetricMembw
        extra_scheduler_kwargs = {"dimensions": set(run_params[1])}

        def task_creation_fun(index):
            return randonly_choose_from_taskset_single(extend_membw_dimensions_to_write_read(tasks__2lm_contention_demo),
                                                       simulator_dimensions, index)

        iterations_data: List[IterationData] = []
        single_run(nodes, task_creation_fun,
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
    # experiment__nodes_membw_contended()
    experiment__ffdassymetricmembw__tco()
