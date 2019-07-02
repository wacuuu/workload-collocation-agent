import json
import os
from collections import defaultdict
from typing import List, Dict, BinaryIO

import ctypes
from dataclasses import dataclass
from wca import perf_const as pc

from wca.metrics import Measurements
from wca.perf import _create_event_attributes, _perf_event_open, _create_file_from_fd, \
    _get_online_cpus, _parse_event_groups, _aggregate_measurements, LIBC
import time


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


if __name__ == '__main__':
    from os.path import join
    base_path = '/sys/devices'

    imcs = [d for d in os.listdir(base_path) if d.startswith('uncore_imc_')]
    pmu_types = [int(open(join(base_path, imc, 'type')).read().rstrip()) for imc in imcs]
    pmu_cpus_set = set([open(join(base_path, imc, 'cpumask')).read().rstrip() for imc in imcs])
    assert len(pmu_cpus_set) == 1
    pmu_cpus_csv = list(pmu_cpus_set)[0]
    cpus = list(map(int, pmu_cpus_csv.split(',')))

    events = [
        Event(name='pmm_bandwidth_read', event=0xe3),
        Event(name='pmm_bandwidth_write', event=0xe7),
        # does work because of group !!!
        Event(name='cas_count_read', event=0x04, umask=0x3),
        Event(name='cas_count_write', event=0x04, umask=0xc),
    ]

    upc = UncorePerfCounters(
        cpus=cpus,
        pmu_events={pmu: events for pmu in pmu_types}

    )
    while True:
        print(json.dumps(upc.get_measurements(), indent=4))
        time.sleep(1)
