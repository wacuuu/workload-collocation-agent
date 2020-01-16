import pytest

from wca.scheduler.algorithms.ffd_generic import FFDGeneric
from wca.scheduler.cluster_simulator import ClusterSimulator, Node, Resources, GB, Task
from wca.scheduler.data_providers.cluster_simulator_data_provider import (
        ClusterSimulatorDataProvider)
from wca.scheduler.types import ResourceType


def create_stressng(i):
    r = Resources(cpu=8, mem=10*GB, membw=20*GB)
    t = Task('stress_ng_{}'.format(i), r)
    return t


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


def create_apache_pass():
    return Node('0', Resources(96, 1000 * GB, 50 * GB))


def create_standard():
    return Node('1', Resources(96, 150 * GB, 150 * GB))


@pytest.mark.parametrize(
    'scheduler_dimensions, expected_all_assigned_count',
    (
        ((ResourceType.CPU, ResourceType.MEM), 9),
        ((ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW), 9),
    )
)
def test_simulator(scheduler_dimensions, expected_all_assigned_count):
    simulator = ClusterSimulator(
        tasks=[],
        nodes=[create_apache_pass(), create_standard()],
        scheduler=None)

    simulator.scheduler = FFDGeneric(data_provider=ClusterSimulatorDataProvider(simulator))

    simulator.reset()
    all_assigned_count = 0
    assigned_count = -1
    iteration = 0

    while assigned_count != 0:
        assigned_count = simulator.iterate_single_task(create_stressng(iteration))
        all_assigned_count += assigned_count
        iteration += 1

    assert all_assigned_count == expected_all_assigned_count


def perform_experiment():
    """Compare standard algorithm with the algorithm which looks also at MEMBW"""
    simulator=ClusterSimulator(
        tasks=[],
        nodes=[create_apache_pass(), create_standard()],
        scheduler=None,
        allow_rough_assignment=True)        
    simulator.scheduler = FFDGeneric(data_provider=ClusterSimulatorDataProvider(simulator))

    for dimensions in ((ResourceType.CPU, ResourceType.MEM),
                       (ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW)):
        simulator.reset()
        simulator.scheduler.resources = dimensions

        all_assigned_count = 0
        assigned_count = -1
        iteration = 0

        while assigned_count != 0:
            assigned_count = simulator.iterate_single_task(create_stressng(iteration))
            all_assigned_count += assigned_count
            iteration += 1


def test_perform_experiment():
    perform_experiment()
