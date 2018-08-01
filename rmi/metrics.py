from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Union


class MetricName(str, Enum):
    INSTRUCTIONS = 'instructions'
    CYCLES = 'cycles'
    CACHE_MISSES = 'cache_misses'
    CPU_USAGE = 'cpu_usage'  # cpuacct.usage (total kernel and user space) in [ns]
    MEM_BW = 'memory_bandwidth'  # counter like [bytes]
    MEM_USAGE = 'memory_usage'


class MetricType(str, Enum):
    GAUGE = 'gauge'      # arbitrary value (can go up and down)
    COUNTER = 'counter'  # monotonically increasing counter


MetricValue = Union[float, int]


@dataclass
class Metric:
    name: Union[str, MetricName]
    value: MetricValue
    labels: Dict[str, str] = field(default_factory=dict)
    type: MetricType = None
    help: str = None


Measurements = Dict[MetricName, MetricValue]
