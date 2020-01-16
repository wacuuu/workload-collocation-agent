import pytest

from wca.scheduler.algorithms.data_proxy import SimulatorDataProxy
from wca.scheduler.algorithms.ffd_generic import FFDGeneric, ResourceType
from wca.scheduler.algorithms.simulator import Simulator, Node, Resources, GB, Task


def create_stressng(i):
    r = Resources(cpu=8, ram=10*GB, membw=20*GB)
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


def set_data_proxy(simulator):
    data_provider = SimulatorDataProxy(simulator)
    free_space_for_resource = data_provider.get_free_space_for_resource
    requested_resource_for_app = data_provider.get_requested_resource_for_app
    # ---
    simulator.scheduler.free_space_for_resource = free_space_for_resource
    simulator.scheduler.requested_resource_for_app = requested_resource_for_app
    

@pytest.mark.parametrize(
    'scheduler_dimensions, expected_all_assigned_count',
    (
        ((ResourceType.CPU, ResourceType.MEM), 9),
        ((ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW), 9),
    )
)
def test_simulator(scheduler_dimensions, expected_all_assigned_count):
    simulator = Simulator(
        tasks=[],
        nodes=[create_apache_pass(), create_standard()],
        scheduler=FFDGeneric())

    set_data_proxy(simulator)

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
    simulator=Simulator(
        tasks=[],
        nodes=[create_apache_pass(), create_standard()],
        scheduler=FFDGeneric(),
        allow_rough_assignment=True)        
    set_data_proxy(simulator)

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
        import ipdb; ipdb.set_trace()


def test_perform_experiment():
    perform_experiment()

