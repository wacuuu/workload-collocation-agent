import logging
from pprint import pprint
from typing import List
import random

from dataclasses import dataclass

from wca.allocators import Allocator, TasksAllocations  # , RDTAllocation
from wca.detectors import TasksMeasurements, TasksResources, TasksLabels, Anomaly
from wca.metrics import Metric
from wca.platforms import Platform

log = logging.getLogger(__name__)


@dataclass
class NUMAAllocator(Allocator):

    def allocate(
            self,
            platform: Platform,
            tasks_measurements: TasksMeasurements,
            tasks_resources: TasksResources,
            tasks_labels: TasksLabels,
            tasks_allocations: TasksAllocations,
    ) -> (TasksAllocations, List[Anomaly], List[Metric]):
        log.info('NUMA allocator random policy here....')
        log.debug('NUMA allocator input data:')

        print('Measurements:')
        pprint(tasks_measurements)
        print('Resources:')
        pprint(tasks_resources)
        print('Labels:')
        pprint(tasks_labels)
        print('Allocations (current):')
        pprint(tasks_allocations)
        pprint(platform)

        # Example stupid policy
        cpu1 = random.randint(0, platform.cpus-1)
        cpu2 = random.randint(0, platform.cpus-1)
        cpu1, cpu2 = sorted([cpu1, cpu2])
        log.debug('random cpus: %s-%s', cpu1, cpu2)

        allocations = {
            'task1': {
                'cpu_set': '%s-%s' % (cpu1, cpu2),
                # Other options:
                # 'cpu_quota': 0.5,
                # 'cpu_shares': 20,
                # only when rdt is enabled!
                # 'rdt': RDTAllocation(
                #     name = 'be',
                #     l3 = '0:10,1:110',
                #     mb = '0:100,1:20',
                # )
            }
        }

        # You can put any metrics here for debugging purposes.
        extra_metrics = [Metric('some_debug', value=1)]

        return allocations, [], extra_metrics
