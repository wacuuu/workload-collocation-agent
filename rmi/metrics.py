from enum import Enum
from dataclasses import dataclass
from typing import Dict, Union


class MetricName(Enum, str):
    INSTRUCTIONS = 'instructions'
    CYCLES = 'cycles'
    LLC_MISSES = 'cache_misses'
    CPU_USAGE = 'cpu_usage'  # cpuacct.usage (total kernel and user space) in [ns]
    MEM_BW = 'memory_bandwidth'  # counter like [bytes]


class MetricType(Enum, str):
    GAUGE = 'gauge'      # arbitrary value (can go up and down)
    COUNTER = 'counter'  # monotonically increasing counter


MetricValue = Union[float, int]


@dataclass
class Metric:
    name: Union[str, MetricName]
    value: MetricValue
    labels: Dict[str, str]
    type: MetricType = None
    help: str = None


MetricValues = Dict[MetricName, MetricValue]
