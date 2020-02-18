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

import os
import logging
import itertools
from typing import Dict, List, Callable, Tuple
import shutil

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.algorithms.bar import BARGeneric
from wca.scheduler.algorithms.fit import FitGeneric
from wca.scheduler.algorithms.nop_algorithm import NOPAlgorithm
from wca.scheduler.cluster_simulator import \
        ClusterSimulator, Node, Resources, Task
from wca.scheduler.data_providers.cluster_simulator_data_provider import (
    ClusterSimulatorDataProvider)
from wca.scheduler.simulator_experiments.nodes_generators import prepare_nodes
from wca.scheduler.simulator_experiments.reporting import IterationData, create_report, print_stats, \
    wrapper_iteration_finished_callback
from wca.scheduler.simulator_experiments.task_generators import TaskGenerator_classes, \
    TaskGenerator_equal
from wca.scheduler.types import ResourceType as rt

log = logging.getLogger(__name__)


def experiments_set__generic(experiment_name, extra_charts, *args):
    """takes the same arguments as experiment__generic but as lists. @TODO"""

    reports_root_directory: str = 'experiments_results'
    stats_dicts = []
    def experiment__generic(
                exp_iter: int,
                max_iteration: int,
                task_creation_fun_def: Tuple[Callable, Dict],
                nodes: List[Node],
                scheduler_init: Tuple[Algorithm, Dict],
                ):
        scheduler_class, scheduler_kwargs = scheduler_init
        input_args = locals()
        iterations_data: List[IterationData] = []

        simulator = ClusterSimulator(tasks=[], nodes=nodes, scheduler=None)
        data_proxy = ClusterSimulatorDataProvider(simulator)
        simulator.scheduler = scheduler_class(data_provider=data_proxy, **scheduler_kwargs)

        task_creation_class, task_creation_args = task_creation_fun_def
        task_creation_fun = task_creation_class(**task_creation_args)

        run_n_iter(max_iteration, simulator, task_creation_fun,
                   wrapper_iteration_finished_callback(iterations_data))

        if extra_charts:
            filter_metrics = simulator.scheduler.get_metrics_names()
        else:
            filter_metrics = []


        args = ',' + '_'.join(['%s_%s'%(k,v)
                               for k,v in scheduler_kwargs.items() if k not in ['dimensions']])
        dimensions = len(scheduler_kwargs.get('dimensions', []))
        stats = create_report(experiment_name,
                      '%d_%s_%s' % (exp_iter, task_creation_fun, simulator.scheduler),
                              input_args, iterations_data,
                              reports_root_directory=reports_root_directory,
                              filter_metrics=filter_metrics,
                              task_gen=task_creation_fun,
                              scheduler=simulator.scheduler,
                              )
        log.debug('Finished experiment.', experiment_name, exp_iter)
        log.debug('Stats:', stats)
        stats_dicts.append(stats)

    if os.path.isdir('experiments_results/{}'.format(experiment_name)):
        shutil.rmtree('experiments_results/{}'.format(experiment_name))
    for exp_iter, params in enumerate(itertools.product(*args)):
        experiment__generic(exp_iter, *params)


    exp_dir = '{}/{}'.format(reports_root_directory, experiment_name)
    print_stats(stats_dicts, exp_dir)

def run_n_iter(iterations_count: int, simulator: ClusterSimulator,
               task_creation_fun: Callable[[int], Task],
               iteration_finished_callback: Callable):
    iteration = 0
    while iteration < iterations_count:
        simulator.iterate_single_task(task_creation_fun(iteration))
        iteration_finished_callback(iteration, simulator)
        iteration += 1
    return simulator


# taken from 2lm contention demo slides:
# Used to filter out unsed node dimensions
nodes_dimensions = {rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}

# wca_load_balancing_multidemnsional_2lm_v0.2
task_definitions = [
    # Task(name='memcached_big',
    #      requested=Resources({rt.CPU: 2, rt.MEM: 28,
    #                           rt.MEMBW: 1.3, rt.WSS: 1.7})),
    # Task(name='memcached_medium',
    #      requested=Resources({rt.CPU: 2, rt.MEM: 12,
    #                           rt.MEMBW: 1.0, rt.WSS: 1.0})),
    # Task(name='memcached_small',
    #      requested=Resources({rt.CPU: 2, rt.MEM: 2.5,
    #                           rt.MEMBW: 0.4, rt.WSS: 0.4})),
    # # ---
    # Task(name='redis_big',
    #      requested=Resources({rt.CPU: 1, rt.MEM: 29,
    #                           rt.MEMBW: 0.5, rt.WSS: 14})),
    # Task(name='redis_medium',
    #      requested=Resources({rt.CPU: 1, rt.MEM: 11,
    #                           rt.MEMBW: 0.4, rt.WSS: 10})),
    # Task(name='redis_small',
    #      requested=Resources({rt.CPU: 1, rt.MEM: 1.5,
    #                           rt.MEMBW: 0.3, rt.WSS: 1.5})),
    # ---
    # Task(name='stress_stream_big',
    #      requested=Resources({rt.CPU: 3, rt.MEM: 13,
    #                           rt.MEMBW: 18, rt.WSS: 12})),
    # Task(name='stress_stream_medium',
    #      requested=Resources({rt.CPU: 1, rt.MEM: 12,
    #                           rt.MEMBW: 6, rt.WSS: 10})),
    # Task(name='stress_stream_small',
    #      requested=Resources({rt.CPU: 1, rt.MEM: 7,
    #                           rt.MEMBW: 5, rt.WSS: 6})),
    # # ---
    # Task(name='sysbench_big',
    #      requested=Resources({rt.CPU: 3, rt.MEM: 9,
    #                           rt.MEMBW: 13, rt.WSS: 7.5})),
    # Task(name='sysbench_medium',
    #      requested=Resources({rt.CPU: 2, rt.MEM: 2,
    #                           rt.MEMBW: 10, rt.WSS: 2})),
    # Task(name='sysbench_small',
    #      requested=Resources({rt.CPU: 1, rt.MEM: 1,
    #                           rt.MEMBW: 8, rt.WSS: 1}))

    # Artificial workloads
    Task(name='cpu', requested=Resources({rt.CPU: 10, rt.MEM: 50, rt.MEMBW_READ: 2, rt.MEMBW_WRITE:1, rt.WSS: 1})),
    Task(name='mem', requested=Resources({rt.CPU: 1, rt.MEM: 100, rt.MEMBW_READ: 1, rt.MEMBW_WRITE:0, rt.WSS: 1})),
    Task(name='mbw', requested=Resources({rt.CPU: 1, rt.MEM: 1,   rt.MEMBW_READ: 10, rt.MEMBW_WRITE:5, rt.WSS: 1})),
]

nodes_definitions = dict(
    aep={rt.CPU: 40, rt.MEM: 1000, rt.MEMBW: 40, rt.MEMBW_READ: 40, rt.MEMBW_WRITE: 10},
    dram={rt.CPU: 40, rt.MEM: 192, rt.MEMBW: 200, rt.MEMBW_READ: 150, rt.MEMBW_WRITE: 150},
)

TASK_SCALE = 4
MACHINE_SCALE = 1

def run():
    # dimensions supported by simulator
    experiments_set__generic(
        'comparing_bar2d_vs_bar3d__option_A',
        False, # extra chart for every metric generated by algorithm
        (30 * TASK_SCALE,),
        (
            (TaskGenerator_equal, dict(task_definitions=task_definitions, replicas=10 * TASK_SCALE)),
            # (TaskGenerator_equal, dict(task_definitions=task_definitions, replicas=15)),
            (TaskGenerator_classes, dict(task_definitions=task_definitions, counts=dict(mbw=3 * TASK_SCALE, cpu=12 * TASK_SCALE, mem=15 * TASK_SCALE))),
            (TaskGenerator_classes, dict(task_definitions=task_definitions, counts=dict(mbw=20 * TASK_SCALE, cpu=5 * TASK_SCALE, mem=5 * TASK_SCALE))),
            (TaskGenerator_classes, dict(task_definitions=task_definitions, counts=dict(mbw=30 * TASK_SCALE, cpu=0 * TASK_SCALE, mem=0 * TASK_SCALE))),
            (TaskGenerator_classes, dict(task_definitions=task_definitions, counts=dict(mbw=0 * TASK_SCALE, cpu=0 * TASK_SCALE, mem=30 * TASK_SCALE))),
            # (TaskGenerator_equal, dict(task_definitions=task_definitions, replicas=50)),
            # (TaskGenerator_random, dict(task_definitions=task_definitions, max_items=200, seed=300)),
        ),
        (
            prepare_nodes(nodes_definitions,
                dict(aep=0, dram=6*MACHINE_SCALE),
                nodes_dimensions,
            ),
            prepare_nodes(nodes_definitions,
                dict(aep=2*MACHINE_SCALE, dram=6*MACHINE_SCALE),
                nodes_dimensions,
            ),
            prepare_nodes(nodes_definitions,
                dict(aep=0, dram=8*MACHINE_SCALE),
                nodes_dimensions,
            ),
            # prepare_nodes(dict(
            #     apache_pass={rt.CPU: 40, rt.MEM: 1000, rt.MEMBW: 40, rt.MEMBW_READ: 40,
            #                  rt.MEMBW_WRITE: 10, rt.WSS: 256},
            #     dram_only_v1={rt.CPU: 48, rt.MEM: 192, rt.MEMBW: 200, rt.MEMBW_READ: 150,
            #                   rt.MEMBW_WRITE: 150, rt.WSS: 192},
            #     dram_only_v2={rt.CPU: 40, rt.MEM: 394, rt.MEMBW: 200, rt.MEMBW_READ: 200,
            #                   rt.MEMBW_WRITE: 200, rt.WSS: 394}),
            #     dict(apache_pass=5, dram_only_v1=10, dram_only_v2=5),
            #     nodes_dimensions
            # ),
        ),
        (
            # (NOPAlgorithm, {}),
            # (FitGeneric, dict(dimensions={rt.CPU, rt.MEM})),
            # (BARGeneric, dict(dimensions={rt.CPU, rt.MEM}, least_used_weight=0)),
            (BARGeneric, dict(alias='baseline', dimensions={rt.CPU, rt.MEM}, least_used_weight=1)),
            # (FitGeneric, dict(dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE})),
            (BARGeneric, dict(alias='extender', dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}, least_used_weight=1)),
            # (BARGeneric, dict(dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}, least_used_weight=0)),
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
    logging.basicConfig(level=logging.INFO)
    # logging.getLogger('wca.scheduler').setLevel(logging.INFO)
    # logging.getLogger('wca.scheduler.cluster_simulator').setLevel(90)
    # logging.getLogger('wca.scheduler.algorithms').setLevel(9)

    run()
