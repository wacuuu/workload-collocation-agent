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

import itertools
import logging
import os
import shutil
from typing import List, Tuple, Callable, Dict, Type

from wca.nodes import Node, Task
from wca.scheduler.algorithms import Algorithm
from wca.scheduler.cluster_simulator import ClusterSimulator
from wca.scheduler.data_providers.cluster_simulator_data_provider import \
    ClusterSimulatorDataProvider
from wca.scheduler.simulator_experiments.reporting import (
    IterationData, wrapper_iteration_finished_callback,
    generate_subexperiment_report, generate_experiment_report)
from wca.scheduler.simulator_experiments.task_generators import TaskGenerator

log = logging.getLogger(__name__)

reports_root_directory: str = 'experiments_results'


def experiments_iterator(exp_name,
                         lengths: List[int], # max iterations
                         task_gen_func_defs: List[Tuple[Type[TaskGenerator], dict]],
                         nodes_sets: List[List[Node]],
                         algorithm_defs: List[Tuple[Type[Algorithm], dict]]
                         ):

    exp_stats: List[dict] = []

    # Recreate results directory.
    exp_dir = '{}/{}'.format(reports_root_directory, exp_name)
    if os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)
    os.makedirs(exp_dir)

    for exp_iter, args in enumerate(itertools.product(
        lengths,
        task_gen_func_defs,
        nodes_sets,
        algorithm_defs
    )):
        length, task_gen_func_def, nodes, algorithm_def = args
        iterations_data, task_gen, simulator = \
            perform_one_experiment(length, task_gen_func_def, nodes, algorithm_def)

        # Sub experiment report
        subexp_title = '%d_%snodes_%s_%s' % (
        exp_iter, len(simulator.nodes), task_gen, simulator.algorithm)
        stats = generate_subexperiment_report(
            exp_name,
            exp_dir,
            subexp_title,
            iterations_data,
            task_gen=task_gen,
            algorithm=simulator.algorithm,
            charts=False,
            extra_charts=False,
        )

        log.debug('Finished experiment.', exp_iter)
        log.debug('Stats:', stats)
        exp_stats.append(stats)

    # Experiment report
    generate_experiment_report(exp_stats, exp_dir)


def perform_one_experiment(
        length: int,
        task_generator_def: Tuple[Callable, Dict],
        nodes: List[Node],
        algorithm_def: Tuple[Type[Algorithm], Dict],
):
    algorithm_class, algorithm_args = algorithm_def
    iterations_data: List[IterationData] = []

    # Back reference between data proxy and simulator.
    simulator = ClusterSimulator(tasks=[], nodes=nodes, algorithm=None)
    data_proxy = ClusterSimulatorDataProvider(simulator)
    simulator.algorithm = algorithm_class(data_provider=data_proxy, **algorithm_args)

    task_gen_class, task_gen_args = task_generator_def
    task_gen = task_gen_class(**task_gen_args)

    run_n_iter(length, simulator, task_gen,
               wrapper_iteration_finished_callback(iterations_data))

    return iterations_data, task_gen, simulator


def run_n_iter(length: int,
               simulator: ClusterSimulator,
               task_gen: Callable[[int], Task],
               iteration_finished_callback: Callable):
    iteration = 0
    while iteration < length:
        simulator.iterate_single_task(task_gen(iteration))
        iteration_finished_callback(iteration, simulator)
        iteration += 1
    return simulator
