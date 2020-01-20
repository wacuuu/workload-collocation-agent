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


def prepare_NxMxK_nodes__demo_configuration(apache_pass_count, dram_only_v1_count, dram_only_v2_count):
    """Taken from wca team real cluster."""
    apache_pass = {ResourceType.CPU: 80, ResourceType.MEM: 1000, ResourceType.MEMBW: 40, ResourceType.WSS=256}
    dram_only_v1 = {ResourceType.CPU: 96, ResourceType.MEM: 192, ResourceType.MEMBW: 150, ResourceType.WSS=192}
    dram_only_v2 = {ResourceType.CPU: 80, ResourceType.MEM: 394, ResourceType.MEMBW: 200, Resource_Type.WSS=394}
    nodes_spec = (apache_pass, dram_only_v1, dram_only_v2)

    inode=0
    nodes = [] 
    for i_node_type, node_type_count in enumerate((apache_pass_count, dram_only_v1, dram_only_v2,)):
        for i in range(node_type_count):
            node = Node(str(inode), available_resources=Resources(nodes_spec[i_note_type]))
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
    while simulator.iterate_single_task(tasks_for_iterations[iteration]) == 1:
        if iteration_finished_callback is not None:
            iteration_finished_callback(iteration, simulator)
        iteration += 1

    return simulator


def experiment__nodes_membw_contended():
    # taken from 2lm contention demo slides:
    # wca_load_balancing_multidemnsional_2lm_v0.2
    tasks = [
        Task(name='memcached_big', 
             requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 28,
                                  ResourceType.MEMBW: 1.3, ResourceType.WSS: 1.7}))
        Task(name='memcached_medium', 
             requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 12,
                                  ResourceType.MEMBW: 1.0, ResourceType.WSS: 1.0}))
        Task(name='memcached_small', 
             requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 2.5,
                                  ResourceType.MEMBW: 0.4, ResourceType.WSS: 0.4}))
        # ---
        Task(name='redis_big',
             requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 29,
                                  ResourceType.MEMBW: 0.5, ResourceType.WSS: 14}))
        Task(name='redis_medium',
             requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 11,
                                  ResourceType.MEMBW: 0.4, ResourceType.WSS: 10}))
        Task(name='redis_small',
             requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1.5,
                                  ResourceType.MEMBW: 0.3, ResourceType.WSS: 1.5}))
        # ---
        Task(name='stress_stream_big',
             requested=Resources({ResourceType.CPU: 3, ResourceType.MEM: 13,
                                  ResourceType.MEMBW: 18, ResourceType.WSS: 12}))
        Task(name='stress_stream_medium',
             requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 12,
                                  ResourceType.MEMBW: 6, ResourceType.WSS: 10}))
        Task(name='stress_stream_small',
             requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 7,
                                  ResourceType.MEMBW: 5, ResourceType.WSS: 6}))
        # ---
        Task(name='sysbench_big',
             requested=Resources({ResourceType.CPU: 3, ResourceType.MEM: 9,
                                  ResourceType.MEMBW: 13, ResourceType.WSS: 7.5}))
        Task(name='sysbench_medium',
             requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 2,
                                  ResourceType.MEMBW: 10, ResourceType.WSS: 2}))
        Task(name='sysbench_small',
             requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1,
                                  ResourceType.MEMBW: 8, ResourceType.WSS: 1}))
    ]
    
    # instead of 3 should be 2, but then results are less visible
    nodes = prepare_NxMxK_nodes__demo_configuration(apache_pass_count=3, dram_only_v1=4, dram_only_v2=2)

    simulator_dimensions = set([ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW,])
    extra_simulator_args = {"allow_rough_assignment": True, "dimensions": simulator_dimensions}
    scheduler_class = FFDGeneric
    extra_scheduler_kwargs = {"dimensions": set([ResourceType.CPU, ResourceType.MEM])}

    @dataclass
    class IterationData:
        cluster_resource_usage: Resources
        per_node_resource_usage: Dict[Node, Resources]
        broken_assignments: Dict[Node, int]

    iterations_data: List[IterationData] = []
    def iteration_finished_callback(iteration: int, simulator: Simulator):
        per_node_resource_usage = simulator.per_node_resource_usage(True)
        cluster_resource_usage = simulator.cluster_resource_usage(True)
        broken_assignments = simulator.rough_assignments_per_node.clone()

        iterations_data.append(IterationData(
            cluster_resource_usage, per_node_resource_usage, broken_assignments))

    simulator = single_run(nodes, tasks_for_iterations,
                           extra_simulator_args, scheduler_class, extra_scheduler_kwargs,
                           iteration_finished_callback)

    def create_report(title, iterations_data: List[IterationData]):
        iter_d= iteration_data
        # only for report generation imports
        import matplotlib.pyplot as plt
        import numpy as np
        plt.style.use('ggplot')

        iterations = np.arange(0, len(iterations_data))
        cpu_usage = np.array([iter_.cluster_resource_usage[ResourceType.CPU] for iter_ in iter_d])
        mem_usage = np.array([iter_.cluster_resource_usage[ResourceType.MEM] for iter_ in iter_d])
        membw_usage = np.array([iter_.cluster_resource_usage[ResourceType.MEMBW] for iter_ in iter_d])
        # ---
        plt.plot(iterations, cpu_usage, 'ro')
        plt.plot(iterations, mem_usage, 'bo')
        plt.plot(iterations, membw_usage, 'go')
        plt.legend(['cpu usage', 'mem usage', 'membw usage'])
        # ---
        plt.xlabel('iteration')
        plt.ylabel('')
        plt.title(title)
        plt.grid(False)
        # ---
        plt.xlim( iterations.min() - 0.01, iterations.max() + 0.01 )
        plt.ylim(min(cpu_usage.min(), mem_usage.min(), membw_usage.min()) - 0.1, 
                 max(cpu_usage.max(), mem_usage.max(), membw_usage.max()) + 0.1)

        plt.savefig('{}.png'.format(title))

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
