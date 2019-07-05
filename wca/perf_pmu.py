import json
import logging
import os
from collections import defaultdict
from enum import Enum
from typing import List, Dict, BinaryIO, Optional

import ctypes
from dataclasses import dataclass
from wca import perf_const as pc

from wca.metrics import Measurements, BaseDerivedMetricsGenerator, BaseGeneratorFactory, \
    EvalBasedMetricsGenerator
from wca.perf import _create_event_attributes, _perf_event_open, _create_file_from_fd, \
    _get_online_cpus, _parse_event_groups, _aggregate_measurements, LIBC
import time


log = logging.getLogger(__name__)

@dataclass
class Event:
    """Similar to man perf list for pmu types unc_imc_0/event=0x,config1=0x/'"""
    event: int
    name: str
    umask: int = 0
    config1: int = 0

    @property
    def config(self) -> int:
        """ head /sys/devices/uncore_imc_0/format/*
        ==> /sys/devices/uncore_imc_0/format/event <==
        config:0-7
        ==> /sys/devices/uncore_imc_0/format/umask <==
        config:8-15
        """
        return self.event | (self.umask << 8)


def _create_event_attributes(pmu_type, disabled, event: Event):
    """Creates perf_event_attr structure for perf_event_open syscall"""
    attr = pc.PerfEventAttr()
    attr.size = pc.PERF_ATTR_SIZE_VER5
    attr.type = pmu_type
    attr.config = event.config
    attr.config1 = event.config1
    attr.sample_type = pc.PERF_SAMPLE_IDENTIFIER
    attr.read_format = (pc.PERF_FORMAT_GROUP |
                        pc.PERF_FORMAT_TOTAL_TIME_ENABLED |
                        pc.PERF_FORMAT_TOTAL_TIME_RUNNING |
                        pc.PERF_FORMAT_ID)
    # attr.read_format = ( pc.PERF_FORMAT_TOTAL_TIME_ENABLED |
    #                     pc.PERF_FORMAT_TOTAL_TIME_RUNNING )

    #attr.flags = pc.AttrFlags.exclude_guest
    attr.flags = pc.AttrFlags.inherit

    if disabled:
        attr.flags |= pc.AttrFlags.disabled

    return attr

@dataclass
class UncorePerfCounters:
    """Perf facade on perf_event_open system call to deal with uncore counters"""
    cpus: List[int]
    pmu_events: Dict[int, List[Event]]  # pmu_type to event_config

    def __post_init__(self):
        # all perf file descriptors, except leaders
        self._event_files: List[BinaryIO] = []
        # perf data file descriptors (only leaders) per pmu and per cpu
        self._group_event_leader_files_per_pmu: Dict[int, Dict[int, BinaryIO]] = defaultdict(
            lambda: defaultdict())
        # DO the magic and enabled everything + start counting
        self._open()

    def get_measurements(self) -> Measurements:
        """Reads, scales and aggregates event measurements"""
        scaled_measurements_and_factor_per_cpu: Dict[int, Measurements] = {}
        scaled_measurements_and_factor_per_pmu: Dict[int, Measurements] = {}

        event_names = []
        for pmu, events in self.pmu_events.items():
            event_names = [e.name for e in events]
            for cpu, event_leader_file in self._group_event_leader_files_per_pmu[pmu].items():
                scaled_measurements_and_factor_per_cpu[cpu] = _parse_event_groups(event_leader_file,
                                                                                  event_names)
            scaled_measurements_and_factor_per_pmu[pmu] = _aggregate_measurements(
                scaled_measurements_and_factor_per_cpu, event_names)

        measurements = _aggregate_measurements(scaled_measurements_and_factor_per_pmu,
                                               event_names)

        return measurements


    def cleanup(self):
        """Closes all opened file descriptors"""
        for pmu, _group_event_leader_files in self._group_event_leader_files_per_pmu.values():
            for file in _group_event_leader_files:
                file.close()
        for file in self._event_files:
            file.close()


    def _open_for_cpu(self, pmu: int, cpu: int, event: Event):
        """Opens file descriptor for event selected via event_name, for selected cpu"""
        group_file = self._group_event_leader_files_per_pmu.get(pmu, {}).get(cpu)
        is_group_leader = group_file is None

        # man perf_event_open cite regarding the disabled variable:
        #   When creating an event group, typically the group leader is
        #     initialized with disabled set to 1 and any child events are
        #     initialized with disabled set to 0.  Despite disabled being 0,
        #     the child events will not start until the group leader is
        #     enabled.
        # Disabled when creating new leader.
        # Enabled for children
        flags = 0  # pc.PERF_FLAG_FD_CLOEXEC
        pid = -1
        if is_group_leader:
            disabled = True
            group_fd = -1
        else:
            disabled = False
            group_fd = group_file.fileno()

        self.attr = _create_event_attributes(
            pmu,
            disabled,
            event,
        )
        pfd = _perf_event_open(perf_event_attr=ctypes.byref(self.attr),
                               pid=pid,
                               cpu=cpu,
                               group_fd=group_fd,
                               flags=flags)
        perf_event_file = _create_file_from_fd(pfd)

        if is_group_leader:
            self._group_event_leader_files_per_pmu[pmu][cpu] = perf_event_file
        else:
            self._event_files.append(perf_event_file)

    def _open(self):
        """Opens file descriptors for selected events, for all online cpus"""
        for pmu, events in self.pmu_events.items():
            for event in events:
                for cpu in self.cpus:
                    self._open_for_cpu(pmu, cpu, event)
            self._reset_and_enable_group_event_leaders(pmu)

    def _reset_and_enable_group_event_leaders(self, pmu):
        for group_event_leader_file in self._group_event_leader_files_per_pmu[pmu].values():
            if LIBC.ioctl(group_event_leader_file.fileno(), pc.PERF_EVENT_IOC_RESET, 0) < 0:
                raise OSError("Cannot reset perf counts")
            if LIBC.ioctl(group_event_leader_file.fileno(), pc.PERF_EVENT_IOC_ENABLE, 0) < 0:
                raise OSError("Cannot enable perf counts")


class UncoreMetricName(str, Enum):
    PMM_BANDWIDTH_READ = 'pmm_bandwidth_read'
    PMM_BANDWIDTH_WRITE = 'pmm_bandwidth_write'
    CAS_COUNT_READ = 'cas_count_read'
    CAS_COUNT_WRITE = 'cas_count_write'


UNCORE_IMC_EVENTS = [
    Event(name=UncoreMetricName.PMM_BANDWIDTH_READ, event=0xe3),
    Event(name=UncoreMetricName.PMM_BANDWIDTH_WRITE, event=0xe7),
    Event(name=UncoreMetricName.CAS_COUNT_READ, event=0x04, umask=0x3),  # * 64 to get bytes
    Event(name=UncoreMetricName.CAS_COUNT_WRITE, event=0x04, umask=0xc),  # * 64 to get bytes
]

def _discover_pmu_uncore_imc_config(events):
    from os.path import join
    base_path = '/sys/devices'
    imcs = [d for d in os.listdir(base_path) if d.startswith('uncore_imc_')]
    pmu_types = [int(open(join(base_path, imc, 'type')).read().rstrip()) for imc in imcs]
    pmu_cpus_set = set([open(join(base_path, imc, 'cpumask')).read().rstrip() for imc in imcs])
    assert len(pmu_cpus_set) == 1
    pmu_cpus_csv = list(pmu_cpus_set)[0]
    cpus = list(map(int, pmu_cpus_csv.split(',')))
    pmu_events = {pmu: events for pmu in pmu_types}
    return cpus, pmu_events


class UncoreDerivedMetricsGenerator(BaseDerivedMetricsGenerator):

    def _derive(self, measurements, delta, available, time_delta):
        scale = 64 / (1024*1024)
        if available(UncoreMetricName.PMM_BANDWIDTH_WRITE, UncoreMetricName.PMM_BANDWIDTH_READ):
            pmm_reads_delta, pmm_writes_delta = delta(UncoreMetricName.PMM_BANDWIDTH_READ, UncoreMetricName.PMM_BANDWIDTH_WRITE)
            measurements['pmm_read_mb_per_second'] = pmm_reads_delta * scale / time_delta
            measurements['pmm_write_mb_per_second'] = pmm_writes_delta * scale / time_delta
            measurements['pmm_total_mb_per_second'] = measurements['pmm_read_mb_per_second'] + measurements['pmm_write_mb_per_second']
        else:
            log.warning('pmm metrics not available!')

        cas_reads_delta, cas_writes_delta = delta(UncoreMetricName.CAS_COUNT_READ, UncoreMetricName.CAS_COUNT_WRITE)
        measurements['dram_read_mb_per_second'] = cas_reads_delta * scale / time_delta
        measurements['dram_write_mb_per_second'] = cas_writes_delta * scale / time_delta
        measurements['dram_total_mb_per_second'] = measurements['dram_read_mb_per_second'] + measurements['dram_write_mb_per_second']


@dataclass
class DefaultPlatformDerivedMetricsGeneratorsFactory(BaseGeneratorFactory):

    extra_metrics: Optional[Dict[str, str]] = None

    def create(self, get_measurements):
        uncore_generator = UncoreDerivedMetricsGenerator(get_measurements)
        if self.extra_metrics:
            return EvalBasedMetricsGenerator(uncore_generator.get_measurements, self.extra_metrics)
        else:
            return uncore_generator

if __name__ == '__main__':
    cpus, pmu_events = _discover_pmu_uncore_imc_config(UNCORE_IMC_EVENTS)

    upc = UncorePerfCounters(
        cpus=cpus,
        pmu_events=pmu_events
    )

    g = DefaultPlatformDerivedMetricsGeneratorsFactory(
        extra_metrics=dict(
            rw_ratio='cas_count_read/cas_count_write'
        )
    ).create(upc.get_measurements)

    while True:
        print(json.dumps(g.get_measurements(), indent=4))
        time.sleep(1)
