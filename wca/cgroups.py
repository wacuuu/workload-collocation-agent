# Copyright (c) 2018 Intel Corporation
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
import os
from enum import Enum
from typing import Optional, List, Union

from dataclasses import dataclass

from wca import logger
from wca.allocations import MissingAllocationException
from wca.allocators import TaskAllocations, AllocationType, AllocationConfiguration
from wca.metrics import Measurements, MetricName, MissingMeasurementException

log = logging.getLogger(__name__)

TASKS = 'tasks'

QUOTA_CLOSE_TO_ZERO_SENSITIVITY = 0.01

# Constants (range limits0 when dealing with cgroups quota and shares.
MIN_SHARES = 2
QUOTA_NOT_SET = -1
QUOTA_MINIMUM_VALUE = 1000
QUOTA_NORMALIZED_MAX = 1.0


class CgroupSubsystem(str, Enum):
    CPU = '/sys/fs/cgroup/cpu'
    CPUSET = '/sys/fs/cgroup/cpuset'
    PERF_EVENT = '/sys/fs/cgroup/perf_event'
    MEMORY = '/sys/fs/cgroup/memory'

    def __repr__(self):
        return repr(self.value)


class CgroupType(str, Enum):
    CPU = 'cpu'
    CPUSET = 'cpuset'
    PERF_EVENT = 'perf_event'
    MEMORY = 'memory'

    def __repr__(self):
        return repr(self.value)


class CgroupResource(str, Enum):
    CPU_USAGE = 'cpuacct.usage'
    CPU_QUOTA = 'cpu.cfs_quota_us'
    CPU_PERIOD = 'cpu.cfs_period_us'
    CPU_SHARES = 'cpu.shares'
    CPUSET_CPUS = 'cpuset.cpus'
    CPUSET_MEMS = 'cpuset.mems'
    MEMORY_USAGE = 'memory.usage_in_bytes'
    MEMORY_MAX_USAGE = 'memory.max_usage_in_bytes'
    MEMORY_LIMIT = 'memory.limit_in_bytes'
    MEMORY_SOFT_LIMIT = 'memory.soft_limit_in_bytes'

    def __repr__(self):
        return repr(self.value)


def _parse_cpuset(value: str) -> List[int]:
    cores = set()

    if not value:
        return list()

    ranges = value.split(',')

    for r in ranges:
        boundaries = r.split('-')

        if len(boundaries) == 1:
            cores.add(int(boundaries[0]))
        elif len(boundaries) == 2:
            start = int(boundaries[0])
            end = int(boundaries[1])

            for i in range(start, end + 1):
                cores.add(i)

    return list(sorted(cores))


def _normalize_cpuset(cores: List[int]) -> str:
    all(isinstance(core, int) for core in cores)
    if len(cores) > 0:
        return str(cores[0])+''.join(','+str(core) for core in cores[1:])
    else:
        return ''


@dataclass
class Cgroup:
    cgroup_path: str

    # Values used for normalization of allocations
    platform_cpus: int = None  # required for quota normalization (None by default until others PRs)
    platform_sockets: int = 0  # required for cpuset.mems
    allocation_configuration: Optional[AllocationConfiguration] = None

    def __post_init__(self):
        assert self.cgroup_path.startswith('/'), 'Provide cgroup_path with leading /'
        relative_cgroup_path = self.cgroup_path[1:]  # cgroup path without leading '/'
        self.cgroup_cpu_fullpath = os.path.join(CgroupSubsystem.CPU, relative_cgroup_path)
        self.cgroup_cpuset_fullpath = os.path.join(CgroupSubsystem.CPUSET, relative_cgroup_path)
        self.cgroup_perf_event_fullpath = os.path.join(
                CgroupSubsystem.PERF_EVENT, relative_cgroup_path)
        self.cgroup_memory_fullpath = os.path.join(CgroupSubsystem.MEMORY,
                                                   relative_cgroup_path)

    def get_measurements(self) -> Measurements:
        try:
            with open(os.path.join(self.cgroup_cpu_fullpath, CgroupResource.CPU_USAGE)) as \
                    cpu_usage_file:
                cpu_usage = int(cpu_usage_file.read())
        except FileNotFoundError as e:
            raise MissingMeasurementException(
                'File {} is missing. Cpu usage unavailable.'.format(e.filename))

        measurements = {MetricName.CPU_USAGE_PER_TASK: cpu_usage}

        for cgroup_resource, metric_name in [
            [CgroupResource.MEMORY_USAGE,      MetricName.MEM_USAGE_PER_TASK],
            [CgroupResource.MEMORY_MAX_USAGE,  MetricName.MEM_MAX_USAGE_PER_TASK],
            [CgroupResource.MEMORY_LIMIT,      MetricName.MEM_LIMIT_PER_TASK],
            [CgroupResource.MEMORY_SOFT_LIMIT, MetricName.MEM_SOFT_LIMIT_PER_TASK],
        ]:

            try:
                with open(os.path.join(self.cgroup_memory_fullpath,
                                       cgroup_resource)) as resource_file:
                    value = int(resource_file.read())
                measurements[metric_name] = value
            except FileNotFoundError as e:
                raise MissingMeasurementException(
                    'File {} is missing. Metric unavailable.'.format(e.filename))


        return measurements

    def _get_proper_path(
            self, cgroup_control_file: str,
            cgroup_control_type: CgroupType) -> str:
        if cgroup_control_type == CgroupType.CPU:
            return os.path.join(self.cgroup_cpu_fullpath, cgroup_control_file)
        if cgroup_control_type == CgroupType.PERF_EVENT:
            return os.path.join(self.cgroup_perf_event_fullpath, cgroup_control_file)
        if cgroup_control_type == CgroupType.CPUSET:
            return os.path.join(self.cgroup_cpuset_fullpath, cgroup_control_file)
        if cgroup_control_type == CgroupType.MEMORY:
            return os.path.join(self.cgroup_cpuset_fullpath,
                                cgroup_control_file)

        raise NotImplementedError(cgroup_control_type)

    def _read_raw(self, cgroup_control_file: str, cgroup_control_type: CgroupType) -> str:
        """Read helper to store any and convert value from cgroup control file."""
        path = self._get_proper_path(cgroup_control_file, cgroup_control_type)
        try:
            with open(path) as file:
                raw_value = file.read()
                log.log(logger.TRACE, 'cgroup: read %s=%r', file.name, raw_value)
        except FileNotFoundError as e:
            raise MissingAllocationException(
                'File {} is missing. Allocation unavailable.'.format(e.filename))

        return raw_value

    def _read(self, cgroup_control_file: str, cgroup_control_type: CgroupType) -> int:
        """Read helper to store any and convert value to int from cgroup control file."""
        raw_value = self._read_raw(cgroup_control_file, cgroup_control_type)
        value = int(raw_value)
        return value

    def _write(
            self, cgroup_control_file: str, value: Union[int, str],
            cgroup_control_type: CgroupType):
        """Write helper to store any int value in cgroup control file."""
        path = self._get_proper_path(cgroup_control_file, cgroup_control_type)
        with open(path, 'wb') as file:
            raw_value = bytes(str(value), encoding='utf8')
            log.log(logger.TRACE, 'cgroup: write %s=%r', file.name, raw_value)
            file.write(raw_value)

    def _get_normalized_shares(self) -> float:
        """Return normalized using cpu_shares and cpu_shares_unit for normalization."""
        assert self.allocation_configuration is not None, \
            'normalization configuration cannot be used without configuration!'
        shares = self._read(CgroupResource.CPU_SHARES, CgroupType.CPU)
        return shares / self.allocation_configuration.cpu_shares_unit

    def _get_normalized_quota(self) -> float:
        """Read normalized quota against configured period and number of available cpus."""
        assert self.allocation_configuration is not None, \
            'normalization configuration cannot be used without configuration!'
        current_quota = self._read(CgroupResource.CPU_QUOTA, CgroupType.CPU)
        current_period = self._read(CgroupResource.CPU_PERIOD, CgroupType.CPU)

        if current_quota == QUOTA_NOT_SET:
            return QUOTA_NORMALIZED_MAX
        # Period 0 is invalid argument for cgroup cpu subsystem. so division is safe.
        return current_quota / current_period / self.platform_cpus

    def get_allocations(self) -> TaskAllocations:
        assert self.allocation_configuration is not None, \
            'reading normalized allocations is not possible without configuration!'
        return {
            AllocationType.QUOTA: self._get_normalized_quota(),
            AllocationType.SHARES: self._get_normalized_shares(),
            AllocationType.CPUSET: self._get_cpuset(),
        }

    def get_pids(self) -> List[str]:
        try:
            with open(os.path.join(self.cgroup_cpu_fullpath, TASKS)) as file:
                return list(file.read().splitlines())
        except FileNotFoundError:
            log.debug('Soft warning: cgroup disappeard during sync, ignore it.')
            return []

    def set_shares(self, normalized_shares: float):
        """Store shares normalized values in cgroup files system. For de-normalization,
        we use reverse formula to _get_normalized_shares."""
        assert self.allocation_configuration is not None, \
            'allocation configuration cannot be used without configuration!'

        shares = int(normalized_shares * self.allocation_configuration.cpu_shares_unit)
        if shares < MIN_SHARES:
            log.warning('cpu.shares smaller than allowed minimum. '
                        'Setting cpu.shares to allowed minimum: '
                        '{}'.format(MIN_SHARES))
            shares = MIN_SHARES

        self._write(CgroupResource.CPU_SHARES, shares, CgroupType.CPU)

    def set_quota(self, normalized_quota: float):
        """Unconditionally sets quota and period if necessary."""
        assert self.allocation_configuration is not None, \
            'setting quota cannot be used without configuration!'
        current_period = self._read(CgroupResource.CPU_PERIOD, CgroupType.CPU)

        if current_period != self.allocation_configuration.cpu_quota_period:
            self._write(
                    CgroupResource.CPU_PERIOD, self.allocation_configuration.cpu_quota_period,
                    CgroupType.CPU)

        if normalized_quota >= QUOTA_NORMALIZED_MAX:
            if normalized_quota > QUOTA_NORMALIZED_MAX:
                log.warning('Quota greater than allowed. Not setting quota.')
            quota = QUOTA_NOT_SET
        else:
            # synchronize period if necessary
            quota = int(normalized_quota * self.allocation_configuration.cpu_quota_period *
                        self.platform_cpus)
            # Minimum quota detected
            if quota < QUOTA_MINIMUM_VALUE:
                log.warning('Quota is smaller than allowed minimum. '
                            'Setting quota value to allowed minimum: '
                            '{}'.format(QUOTA_MINIMUM_VALUE))
                quota = QUOTA_MINIMUM_VALUE

        self._write(CgroupResource.CPU_QUOTA, quota, CgroupType.CPU)

    def set_cpuset(self, cpus: str, mems: str):
        """Set cpuset.cpus and cpuset.mems."""
        normalized_cpus = _normalize_cpuset(cpus)
        normalized_mems = _normalize_cpuset(mems)

        assert normalized_cpus is not None
        assert normalized_mems is not None

        try:
            self._write(CgroupResource.CPUSET_CPUS, normalized_cpus, CgroupType.CPUSET)
        except PermissionError:
            log.warning(
                    'Cannot write {}: "{}" to "{}"! Permission denied.'.format(
                        CgroupResource.CPUSET_CPUS, normalized_cpus, self.cgroup_cpuset_fullpath))
        try:
            self._write(CgroupResource.CPUSET_MEMS, normalized_mems, CgroupType.CPUSET)
        except PermissionError:
            log.warning(
                    'Cannot write {}: "{}" to "{}"! Permission denied.'.format(
                        CgroupResource.CPUSET_MEMS, normalized_mems, self.cgroup_cpuset_fullpath))

    def _get_cpuset(self) -> str:
        """Get current cpuset.cpus."""

        try:
            cpus = _parse_cpuset(self._read_raw(CgroupResource.CPUSET_CPUS,
                                                CgroupType.CPUSET).strip())
            return _normalize_cpuset(cpus)
        except PermissionError:
            log.warning(
                    'Cannot read {}: "{}"! Permission denied.'.format(
                        CgroupResource.CPUSET_CPUS, self.cgroup_cpuset_fullpath))
