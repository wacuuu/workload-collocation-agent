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
from wca.scheduler.simulator_experiments.experiment_1 import single_run


def test_perform_experiment():
    simulator_dimensions = set([ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW,])
    nodes = [Node('0', Resources({ResourceType.CPU: 96, ResourceType.MEM: 1000, ResourceType.MEMBW: 50})),
             Node('1', Resources({ResourceType.CPU: 96, ResourceType.MEM: 320, ResourceType.MEMBW: 150}))]
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
