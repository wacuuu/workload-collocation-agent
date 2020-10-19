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

from typing import Dict, List, Tuple
from connection import PrometheusClient
from model import Task, Node
from metrics import Metric, MetricsQueries, Function, FunctionsDescription


def build_function_call_id(function: Function, arg: str):
    return "{}{}".format(FunctionsDescription[function], str(arg))


class AnalyzerQueries:
    """Class used for namespace"""

    def __init__(self, prometheus_url):
        self.prometheus_client = PrometheusClient(prometheus_url)

    def query_tasks_list(self, time) -> Dict[str, Task]:
        query_result = self.prometheus_client.instant_query(MetricsQueries[Metric.TASK_UP], time)
        tasks = {}
        for metric in query_result:
            metric = metric['metric']
            task_name = metric['task_name']
            tasks[task_name] = Task(metric['task_name'], metric['app'],
                                    metric['nodename'])
        return tasks

    def query_platform_performance_metrics(self, time: int, nodes: Dict[str, Node]):
        # very important parameter - window_length [s]

        metrics = (Metric.PLATFORM_MEM_USAGE, Metric.PLATFORM_CPU_REQUESTED,
                   Metric.PLATFORM_CPU_UTIL, Metric.PLATFORM_MBW_TOTAL,
                   Metric.POD_SCHEDULED, Metric.PLATFORM_DRAM_HIT_RATIO, Metric.PLATFORM_WSS_USED)

        for metric in metrics:
            query_results = self.prometheus_client.instant_query(MetricsQueries[metric], time)
            for result in query_results:
                nodes[result['metric']['nodename']].performance_metrics[metric] = \
                    {'instant': result['value'][1]}

    def query_performance_metrics(self, time: int, functions_args: Dict[Metric, List[Tuple]],
                                  metrics: List[Metric], window_length: int) -> Dict[Metric, Dict]:
        """performance metrics which needs aggregation over time"""
        query_results: Dict[Metric, Dict] = {}
        for metric in metrics:
            for function in functions_args[metric]:
                query_template = "{function}({arguments}{prom_metric}[{window_length}s])"
                query = query_template.format(function=function[0].value,
                                              arguments=function[1],
                                              window_length=window_length,
                                              prom_metric=MetricsQueries[metric])
                query_result = self.prometheus_client.instant_query(query, time)
                aggregation_name = build_function_call_id(function[0], function[1])

                if metric in query_results:
                    query_results[metric][aggregation_name] = query_result
                else:
                    query_results[metric] = {aggregation_name: query_result}
        return query_results

    def query_task_performance_metrics(self, time: int, tasks: Dict[str, Task],
                                       window_length: int = 120):

        metrics = [Metric.TASK_THROUGHPUT, Metric.TASK_LATENCY,
                   Metric.TASK_MEM_MBW_LOCAL, Metric.TASK_MEM_MBW_REMOTE]
        gauge_function_args = [(Function.AVG, ''), (Function.QUANTILE, '0.1,'),
                               (Function.QUANTILE, '0.9,')]
        counter_function_args = [(Function.RATE, '')]

        function_args = {Metric.TASK_THROUGHPUT: gauge_function_args,
                         Metric.TASK_LATENCY: gauge_function_args,
                         Metric.TASK_MEM_MBW_LOCAL: counter_function_args,
                         Metric.TASK_MEM_MBW_REMOTE: counter_function_args}

        query_results = self.query_performance_metrics(time, function_args, metrics, window_length)
        for metric, query_result in query_results.items():
            for aggregation_name, result in query_result.items():
                for per_app_result in result:
                    task_name = per_app_result['metric']['task_name']
                    value = per_app_result['value'][1]
                    if task_name in tasks and metric in tasks[task_name].performance_metrics:
                        tasks[task_name].performance_metrics[metric][aggregation_name] = value
                    elif task_name in tasks:
                        tasks[task_name].performance_metrics[metric] = {aggregation_name: value}

    def query_task_numa_pages(self, time: int, tasks: Dict[str, Task]):
        query_result = self.prometheus_client.instant_query('{}'.format(
            Metric.TASK_MEM_NUMA_PAGES.value), time)
        for metric in query_result:
            task_name = metric['metric']['task_name']
            value = metric['value'][1]
            numa_node = metric['metric']['numa_node']
            if Metric.TASK_MEM_NUMA_PAGES not in tasks[task_name].performance_metrics:
                tasks[task_name].performance_metrics[Metric.TASK_MEM_NUMA_PAGES] =\
                    {'0': 0, '1': 0, '2': 0, '3': 0}
            tasks[task_name].performance_metrics[Metric.TASK_MEM_NUMA_PAGES][numa_node] = value
