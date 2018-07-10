from typing import List, Dict
from dataclasses import dataclass

from rmi.base import Metric

# 0-based logical processor number (matches the value of "processor" in /proc/cpuinfo)
CpuId = int


@dataclass
class Platform:

    # Topology:
    sockets: int  # number of sockets
    cores: int    # number of physical cores in total (sum over all sockets)
    cpus: int     # logical processors equal to the output of "nproc" Linux command

    # Utilization (usage):
    # counter like, sum of all modes based on /proc/stat
    # "cpu line" with 10ms resolution expressed in [ms]
    cpus_usage: Dict[CpuId, int]

    # [bytes] based on /proc/meminfo (gauge like)
    # difference between MemTotal and MemAvail (or MemFree)
    total_memory_used: int


def collect_platform_information() -> (Platform, List[Metric], Dict[str, str]):
    """Returns Platform infromation, metrics and common_lables."""
    # TODO: implement me
    return Platform(0, 0, 0, {}, 0), [], []
