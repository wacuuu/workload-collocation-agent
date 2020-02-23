# Copyright (c) 2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from wca.logger import TRACE
from wca.scheduler.algorithms.bar import BAR
from wca.scheduler.algorithms.least_used_bar import LeastUsedBAR
from wca.scheduler.algorithms.least_used import LeastUsed
from wca.scheduler.algorithms.hierbar import HierBAR
from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.algorithms.nop_algorithm import NOPAlgorithm
from wca.scheduler.algorithms.static_assigner import StaticAssigner
from wca.scheduler.simulator_experiments import experiments_set__generic
from wca.scheduler.simulator_experiments.nodes_generators import prepare_nodes
from wca.scheduler.simulator_experiments.nodesets import nodes_definitions_2types, \
    nodes_definitions_artificial_2dim_2types, nodes_definitions_3types
from wca.scheduler.simulator_experiments.task_generators import TaskGenerator_equal, \
    TaskGenerator_classes
from wca.scheduler.simulator_experiments.tasksets import task_definitions__artificial_3types, \
    task_definitions__artificial_2dim_2types
from wca.scheduler.simulator_experiments.tasksets import task_definitions__artificial_2, \
    taskset_dimensions
from wca.scheduler.types import ResourceType as rt

log = logging.getLogger(__name__)

dim4 = {rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}
dim2 = {rt.CPU, rt.MEM}


def experiment_debug():
    TASK_SCALE = 1
    CLUSTER_SCALE = 1
    nodes_dimensions = dim4
    experiments_set__generic(
        'debug',
        False,
        (30 * TASK_SCALE,),
        (
            (TaskGenerator_equal,
             dict(task_definitions=task_definitions__artificial_3types, replicas=10 * TASK_SCALE)),
        ),
        (
            prepare_nodes(nodes_definitions_2types, dict(aep=2 * CLUSTER_SCALE, dram=6 * CLUSTER_SCALE),
                          nodes_dimensions, ),
        ),
        (
            (LeastUsedBAR,
             dict(alias='BAR__LU_ON__WEIGHTS_UNUEQUAL', dimensions=dim4, least_used_weight=1,
                  bar_weights={rt.MEM: 0.5})),
            (LeastUsedBAR,
             dict(alias='BAR__LU_ON__WEIGHTS_EQUAL', dimensions=dim4, least_used_weight=1)),
            (LeastUsedBAR,
             dict(alias='BAR__LU_ON__WEIGHTS_100x', dimensions=dim4, least_used_weight=100)),
            (LeastUsedBAR, dict(alias='BAR__LU_OFF', dimensions=dim4, least_used_weight=0)),
        ),
    )


def experiment_bar():
    task_scale = 10
    cluster_scale = 10
    nodes_dimensions = dim4

    experiments_set__generic(
        'bar_weights',
        False,
        (30 * task_scale,),
        (
            (TaskGenerator_classes, dict(task_definitions=task_definitions__artificial_2, counts=dict(mbw=20 * task_scale, cpu=5 * task_scale, mem=5 * task_scale))),
        ),
        (
            prepare_nodes(nodes_definitions_2types, dict(aep=2 * cluster_scale, dram=6 * cluster_scale), nodes_dimensions),
        ),
        (
            (LeastUsedBAR, dict(alias='BAR__LU_ON__WEIGHTS_UNUEQUAL',
                              dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE},
                              least_used_weight=1, bar_weights={rt.MEM: 0.5})),
            (LeastUsedBAR, dict(alias='BAR__LU_ON__WEIGHTS_EQUAL',
                              dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE},
                              least_used_weight=1)),
            (LeastUsedBAR, dict(alias='BAR__LU_ON__WEIGHTS_100x',
                              dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE},
                              least_used_weight=100)),
            (LeastUsedBAR,
             dict(alias='BAR__LU_OFF', dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE},
                  least_used_weight=0)),
        ),
    )


def experiment_full(task_scale=1, cluster_scale=1):
    iterations = 30 * task_scale
    nodes_dimensions = dim4
    experiments_set__generic(
        'intel_demo_local',
        False,  # extra chart for every metric generated by algorithm
        (30 * task_scale,),
        (
            (TaskGenerator_equal, dict(task_definitions=task_definitions__artificial_3types, replicas=10 * task_scale)),
            (TaskGenerator_classes, dict(task_definitions=task_definitions__artificial_3types, counts=dict(mbw=3 * task_scale, cpu=12 * task_scale, mem=15 * task_scale))),
            (TaskGenerator_classes, dict(task_definitions=task_definitions__artificial_3types, counts=dict(mbw=20 * task_scale, cpu=5 * task_scale, mem=5 * task_scale))),
            (TaskGenerator_classes, dict(task_definitions=task_definitions__artificial_3types, counts=dict(mbw=30 * task_scale, cpu=0 * task_scale, mem=0 * task_scale))),
            (TaskGenerator_classes, dict(task_definitions=task_definitions__artificial_3types, counts=dict(mbw=0 * task_scale, cpu=0 * task_scale, mem=30 * task_scale))),
        ),
        (
            prepare_nodes(nodes_definitions_2types, dict(aep=0, dram=6 * cluster_scale), nodes_dimensions),
            prepare_nodes(nodes_definitions_2types, dict(aep=2 * cluster_scale, dram=6 * cluster_scale), nodes_dimensions),
            prepare_nodes(nodes_definitions_2types, dict(aep=0, dram=8 * cluster_scale), nodes_dimensions),
            prepare_nodes(nodes_definitions_2types, dict(aep=cluster_scale, dram=cluster_scale), nodes_dimensions, ),
        ),
        (
            (NOPAlgorithm, {}),
            (Fit, dict(dimensions=dim2)),
            (Fit, dict(dimensions=dim4)),
            (LeastUsed, dict(dimensions=dim2)),
            (LeastUsed, dict(dimensions=dim4)),
            (BAR, dict(dimensions=dim2)),
            (HierBAR, dict(dimensions=dim2)),
            (LeastUsedBAR, dict(alias='kubernetes_baseline', dimensions={rt.CPU, rt.MEM})),
            (LeastUsedBAR, dict(alias='BAR__LU_OFF', dimensions=dim4, least_used_weight=0)),
            (LeastUsedBAR,
             dict(alias='BAR__LU_ON__WEIGHTS_EQUAL', dimensions=dim4, least_used_weight=1)),
            (LeastUsedBAR,
             dict(alias='BAR__LU_ON__WEIGHTS_UNUEQUAL', dimensions=dim4, least_used_weight=1,
                  bar_weights={rt.MEM: 0.5})),
        ),
    )


def experiment_static_assigner():
    nodes_dimensions = dim4
    targeted_assigned_apps_counts = \
        {'aep_0': {'cpu': 1, 'mem': 2, 'mbw': 2},
         'dram_0': {'cpu': 1, 'mem': 0, 'mbw': 0}}

    experiments_set__generic(
        'static_assigner',
        False,
        (6,),
        (
            (TaskGenerator_classes,
             dict(task_definitions=taskset_dimensions(nodes_dimensions,
                                                      task_definitions__artificial_2),
                  counts=dict(mbw=2, cpu=2, mem=2))),
        ),
        (
            prepare_nodes(nodes_definitions_2types,
                          dict(aep=1, dram=1),
                          nodes_dimensions,
                          ),
        ),
        (
            (StaticAssigner,
             dict(alias='StaticAssigner',
                  targeted_assigned_apps_counts=targeted_assigned_apps_counts)),
        ),
    )



def experiment_hierbar():
    nodes_dimensions = dim4
    iterations = 30
    experiments_set__generic(
        'hierbar',
        False,
        (iterations,),
        # [(TaskGenerator_equal, dict(task_definitions=task_definitions__artificial_2dim_2types, replicas=5))],
        # [prepare_nodes(nodes_definitions_artificial_2dim_2types, dict(cpuhost=2, memhost=1), nodes_dimensions)],
        [(TaskGenerator_equal, dict(task_definitions=task_definitions__artificial_3types, replicas=10))],
        [prepare_nodes(nodes_definitions_3types, dict(aep=2, dram_sml=4, dram_big=2), nodes_dimensions)],
        (
            (HierBAR, dict(dimensions=nodes_dimensions)),
        ),
    )

if __name__ == "__main__":
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        # No installed packages required for report generation.
        print('numpy and matplotlib are required!')
        exit(1)

    # init_logging('trace', 'scheduler_extender_simulator_experiments')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(module)s:%(funcName)s:%(lineno)d %(message)s')
    # from wca.logger import TRACE
    # logging.getLogger('wca.scheduler').setLevel(logging.INFO)
    # logging.getLogger('wca.scheduler.cluster_simulator').setLevel(TRACE)
    # logging.getLogger('wca.scheduler.algorithms').setLevel(logging.DEBUG)

    # experiment_debug()
    # experiment_full()
    # logging.getLogger('wca.scheduler.algorithms.hierbar').setLevel(TRACE)
    logging.getLogger('wca.scheduler.algorithms.bar').setLevel(logging.DEBUG)
    logging.getLogger('wca.scheduler.algorithms.hierbar').setLevel(logging.DEBUG)
    experiment_hierbar()
    # experiment_bar() # Does not work !!!
    # experiment_static_assigner()
