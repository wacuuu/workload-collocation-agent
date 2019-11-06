import logging
from typing import List, Dict
import subprocess
# from pprint import pprint

from dataclasses import dataclass

from wca.allocators import Allocator, TasksAllocations, AllocationType
from wca.detectors import TasksMeasurements, TasksResources, TasksLabels, Anomaly
from wca.metrics import Metric, MetricName
from wca.platforms import Platform, encode_listformat, decode_listformat

log = logging.getLogger(__name__)


def migrate_pages(task, tasks_pids, to_node):
    # if not all pages yet on place force them to move
    from_node = str(0 if to_node else 1)
    to_node = str(to_node)
    for pid in tasks_pids[task]:
        pid = str(pid)
        cmd = ['migratepages', pid, from_node, to_node]
        log.debug('migrate pages cmd: %s', ' '.join(cmd))
        subprocess.check_output(cmd)


@dataclass
class NUMAAllocator(Allocator):

    # intrusive set of options
    # parse15
    # preferences_threshold: float = 0.66
    preferences_threshold: float = 0.0  # always migrate
    memory_migrate: bool = True
    memory_migrate_min_task_balance: float = 0.95

    # use candidate
    candidate = True

    def allocate(
            self,
            platform: Platform,
            tasks_measurements: TasksMeasurements,
            tasks_resources: TasksResources,
            tasks_labels: TasksLabels,
            tasks_allocations: TasksAllocations,
            tasks_pids,
    ) -> (TasksAllocations, List[Anomaly], List[Metric]):
        log.info('NUMA allocator Pv5 policy here for %s tasks...', len(tasks_pids))
        # log.debug('NUMA allocator input data :')
        # log.debug('NUMA allocator input data :')
        log.debug('Tasks pids %r', tasks_pids)
        log.debug('Tasks resources %r', tasks_resources)
        #
        # print('Measurements:')
        # pprint(tasks_measurements)
        # print('Resources:')
        # pprint(tasks_resources)
        # print('Labels:')
        # pprint(tasks_labels)
        # print('Allocations (current):')
        # pprint(tasks_allocations)
        # print("Platform")
        # pprint(platform)

        # # Example stupid policy
        # cpu1 = random.randint(0, platform.cpus-1)
        # cpu2 = random.randint(cpu1, platform.cpus-1)
        # log.debug('random cpus: %s-%s', cpu1, cpu2)
        # memory_migrate = random.randint(0, 1)
        # log.debug('random memory_migrate: %s-%s', cpu1, cpu2)
        # allocations = {
        #     'task1': {
        #         AllocationType.CPUSET_CPUS: '%s-%s' % (cpu1, cpu2),
        #         AllocationType.CPUSET_MEMS: '%s-%s' % (cpu1, cpu2),
        #         AllocationType.CPUSET_MEM_MIGRATE: memory_migrate,
        #         # Other options:
        #         # 'cpu_quota': 0.5,
        #         # 'cpu_shares': 20,
        #         # only when rdt is enabled!
        #         # 'rdt': RDTAllocation(
        #         #     name = 'be',
        #         #     l3 = '0:10,1:110',
        #         #     mb = '0:100,1:20',
        #         # )
        #     }
        # }
        # # You can put any metrics here for debugging purposes.

        # print("Policy:")

        allocations = {}

        # Total host memory
        total_memory = _platform_total_memory(platform)
        # print("Total memory: %d\n" % total_memory)
        extra_metrics = []

        # Collect tasks sizes and NUMA node usages
        tasks_memory = []
        for task in tasks_labels:
            tasks_memory.append(
                (task,
                 _get_task_memory_limit(tasks_measurements[task], total_memory, task),
                 _get_numa_node_preferences(tasks_measurements[task], platform)))
        tasks_memory = sorted(tasks_memory, reverse=True, key=lambda x: x[1])

        # FOR DEBUGGING PURPOSES just sort by name (it should work the same assuming
        # memory is equal for all tasks)
        # tasks_memory = sorted(tasks_memory, reverse=False, key=lambda x: x[0])  # by name

        # pprint(tasks_memory)

        # Current state of the system
        balanced_memory = {x: [] for x in platform.measurements[MetricName.MEM_NUMA_USED]}

        balance_task = None
        balance_task_node = None
        balance_task_candidate = None
        balance_task_node_candidate = None

        did_some_migration = False
        # First, get current state of the system
        for task, memory, preferences in tasks_memory:
            current_node = _get_current_node(
                decode_listformat(tasks_allocations[task][AllocationType.CPUSET_CPUS]),
                platform.node_cpus)
            log.debug("Task: %s Memory: %d Preferences: %s, Current node: %d" % (
                task, memory, preferences, current_node))
            if current_node >= 0:
                # log.debug("task already placed, recording state")
                balanced_memory[current_node].append((task, memory))

                task_balance = preferences[current_node]
                if self.memory_migrate and task_balance < self.memory_migrate_min_task_balance:
                    did_some_migration = True
                    log.info('Task: %s Move pages task balance = %r', task, task_balance)
                    try:
                        migrate_pages(task, tasks_pids, current_node)
                    except subprocess.CalledProcessError:
                        log.error('cannot migrate pages pid=%s (task=%s)'
                                  'in this loop: ignored for next loop', tasks_pids, task)
                        log.exception('called process error')

        log.debug("Current state of the system: %s" % balanced_memory)
        log.debug("Current state of the system per node: %s" % {
            node: sum(t[1] for t in tasks)/2**10 for node, tasks in balanced_memory.items()})

        for node, tasks_with_memory in balanced_memory.items():
            extra_metrics.extend([
                Metric('numa__balanced_memory_tasks', value=len(tasks_with_memory),
                       labels=dict(numa_node=str(node))),
                Metric('numa__balanced_memory_size', value=sum([m for t, m in tasks_with_memory]),
                       labels=dict(numa_node=str(node)))
            ])

        if did_some_migration:
            log.debug('Did some migration, wait for another call...')
            # because current state of system is outdate do nothing and wait for another call
            return {}, [], extra_metrics

        log.debug("Starting re-balancing")

        for task, memory, preferences in tasks_memory:
            log.debug("Task: %s Memory: %d Preferences: %s" % (task, memory, preferences))
            current_node = _get_current_node(
                decode_listformat(tasks_allocations[task][AllocationType.CPUSET_CPUS]),
                platform.node_cpus)
            most_used_node = _get_most_used_node(preferences)
            best_memory_node = _get_best_memory_node(memory, balanced_memory)
            most_free_memory_node = \
                _get_most_free_memory_node(memory,
                                           platform.measurements[MetricName.MEM_NUMA_FREE])
            extra_metrics.extend([
                Metric('numa__task_current_node', value=current_node,
                       labels=tasks_labels[task]),
                Metric('numa__task_most_used_node', value=most_used_node,
                       labels=tasks_labels[task]),
                Metric('numa__task_best_memory_node', value=best_memory_node,
                       labels=tasks_labels[task]),
                Metric('numa__task_best_memory_node_preference', value=preferences[most_used_node],
                       labels=tasks_labels[task]),
                Metric('numa__task_most_free_memory_mode', value=most_free_memory_node,
                       labels=tasks_labels[task])
            ])

            # log.debug("Task current node: %d", current_node)
            if current_node >= 0:
                log.debug("   task already placed on the node %d, taking next" % current_node)
                # balanced_memory[current_node].append((task, memory))
                continue

            if memory == 0:
                # Handle missing data for "ghost" tasks
                # e.g. cgroup without processes when using StaticNode
                log.warning(
                    'skip allocation for %r task - not enough data - '
                    'maybe there are no processes there!',
                    task)
                continue

            # print("Most used node: %d" % most_used_node)
            # # memory based score:
            # print("Best memory node: %d" % best_memory_node)
            # print("Best free memory node: %d" % most_free_memory_node)

            log.debug("Task %s: Most used node: %d, Best free node: %d, Best memory node: %d" %
                      (task, most_used_node, most_free_memory_node, best_memory_node))

            # if not yet task found for balancing
            if balance_task is None and balance_task_node is None:

                # Give a chance for AutoNUMA to re-balance memory
                if preferences[most_used_node] < self.preferences_threshold:
                    log.debug("   THRESHOLD: not most of the memory balanced, continue")
                    continue

                if most_used_node == best_memory_node or most_used_node == most_free_memory_node:
                    log.info("   OK: found task for balancing: %s", task)
                    balance_task = task
                    balance_task_node = most_used_node
                    # break # commented to give a chance to generate other metrics

                elif self.candidate and balance_task_candidate is None \
                        and balance_task_node_candidate is None:
                    log.debug("   CANDIT: not perfect match, but remember as candidate, continue")
                    balance_task_candidate = task
                    balance_task_node_candidate = best_memory_node
                    # balance_task_node_candidate = most_free_memory_node

                else:
                    log.debug("   IGNORE: not perfect match and candidate set(disabled), continue")
                # break # commented to give a chance to generate other metrics

            # if most_used_node != most_free_memory_node:
            #     continue

            # pref_nodes = {}
            # for node in preferences:
            #     print(preferences[node])
            #     print(( memory / (sum([k[1] for k in balanced_memory[node]])+memory))/2)
            #     # pref_nodes[node] = max(preferences[node],
            #     #     ( memory / (sum([k[1] for k in balanced_memory[node]])+memory))/2)
            #     pref_nodes[node] = preferences[node]
            #     # pref_nodes[node] = ( memory/(sum([k[1] for k in balanced_memory[node]])+memory))
            # pprint(pref_nodes)
            # best_node = sorted(pref_nodes.items(), reverse=True, key=lambda x: x[1])[0][0]
            # # pprint(best_node)
            # balanced_memory[best_node].append((task, memory))

        # pprint(balanced_memory)
        # print('balance_task to node: ', balance_task, balance_task_node)
        if balance_task is None and balance_task_node is None:
            if balance_task_candidate is not None and balance_task_node_candidate is not None:
                log.info("   Candidate rule: Cannot find by most_used, 'best memory node' rule!")
                balance_task = balance_task_candidate
                balance_task_node = balance_task_node_candidate

        if balance_task is not None and balance_task_node is not None:
            log.info("   Assign task %s to node %s." % (balance_task, balance_task_node))
            allocations[balance_task] = {
                AllocationType.CPUSET_CPUS: encode_listformat(
                    platform.node_cpus[balance_task_node]),
                AllocationType.CPUSET_MEMS: encode_listformat({balance_task_node}),
            }
            # Instant memory migrate.
            # Do not move page immediatly until - cpuset cpus/mems are set in next loop
            # TODO: to be fixed when move pages is moved to WCA internals
            # if self.memory_migrate:
            #     log.debug("Assign task %s to node %s with memory migrate" %
            #               (balance_task, balance_task_node))
            #     allocations[balance_task][AllocationType.CPUSET_MEM_MIGRATE] = 1
            #     migrate_pages(balance_task, tasks_pids, balance_task_node)

        # for node in balanced_memory:
        #     for task, _ in balanced_memory[node]:
        #         if decode_listformat(tasks_allocations[task]['cpu_set']) ==
        #         platform.node_cpus[node]:
        #             continue
        #         allocations[task] = {
        #             AllocationType.CPUSET_MEM_MIGRATE: 1,
        #             AllocationType.CPUSET: platform.node_cpus[node],
        #         }

        # pprint(allocations)

        # for task in tasks_labels:
        #     allocations[task] = {
        #         AllocationType.CPUSET_MEM_MIGRATE: memory_migrate,
        #     }

        return allocations, [], extra_metrics


def _platform_total_memory(platform):
    return sum(platform.measurements[MetricName.MEM_NUMA_FREE].values()) + \
           sum(platform.measurements[MetricName.MEM_NUMA_USED].values())


def _get_task_memory_limit(task_measurements, total, task):
    "Returns detected maximum memory for the task"
    limits_order = [
        MetricName.MEM_LIMIT_PER_TASK,
        MetricName.MEM_SOFT_LIMIT_PER_TASK,
        MetricName.MEM_MAX_USAGE_PER_TASK,
        MetricName.MEM_USAGE_PER_TASK, ]
    for limit in limits_order:
        if limit not in task_measurements:
            continue
        if task_measurements[limit] > total:
            continue
        log.debug('Task: %s limit %s %s %s %s', task, limit, 'is', task_measurements[limit], 'b')
        return task_measurements[limit]
    return 0


def _get_numa_node_preferences(task_measurements, platform: Platform) -> Dict[int, float]:
    ret = {node_id: 0 for node_id in range(0, platform.numa_nodes)}
    if MetricName.MEM_NUMA_STAT_PER_TASK in task_measurements:
        metrics_val_sum = sum(task_measurements[MetricName.MEM_NUMA_STAT_PER_TASK].values())
        for node_id, metric_val in task_measurements[MetricName.MEM_NUMA_STAT_PER_TASK].items():
            ret[int(node_id)] = metric_val / max(1, metrics_val_sum)
    else:
        log.warning('{} metric not available'.format(MetricName.MEM_NUMA_STAT_PER_TASK))
    return ret


def _get_most_used_node(preferences):
    return sorted(preferences.items(), reverse=True, key=lambda x: x[1])[0][0]


def _get_current_node(cpus, nodes):
    for node in nodes:
        if nodes[node] == cpus:
            return node
    return -1


def _get_best_memory_node(memory, balanced_memory):
    """for equal task memory, choose node with less allocated memory by WCA"""
    d = {}
    for node in balanced_memory:
        d[node] = memory / (sum([k[1] for k in balanced_memory[node]]) + memory)
    best = sorted(d.items(), reverse=True, key=lambda x: x[1])
    # print('best:')
    # pprint(best)
    return best[0][0]


def _get_most_free_memory_node(memory, node_memory_free):
    d = {}
    for node in node_memory_free:
        d[node] = memory / node_memory_free[node]
    # pprint(d)
    free_nodes = sorted(d.items(), key=lambda x: x[1])
    # print('free:')
    # pprint(free_nodes)
    return free_nodes[0][0]
