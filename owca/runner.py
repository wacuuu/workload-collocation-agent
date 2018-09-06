from dataclasses import dataclass, field
from typing import List, Dict
import logging
import time


from owca import detectors
from owca import logger
from owca import mesos
from owca import platforms
from owca import storage
from owca.containers import Container
from owca.detectors import TasksMeasurements, convert_anomalies_to_metrics
from owca.mesos import MesosTask, create_metrics
from owca.metrics import Metric
from owca.resctrl import check_resctrl, cleanup_resctrl
from owca.perf import are_privileges_sufficient

log = logging.getLogger(__name__)


def _calculate_desired_state(
        discovered_tasks: List[MesosTask], known_containers: List[Container]
        ) -> (List[MesosTask], List[Container]):
    """Prepare desired state of system by comparing actual running Mesos tasks and already
    watched containers.

    Assumptions:
    * One-to-one relationship between task and container
    * cgroup_path for task and container need to be identical to establish the relationship
    * cgroup_path is unique for each task

    :returns "list of Mesos tasks to start watching" and "orphaned containers to cleanup" (there are
    no more Mesos tasks matching those containers)
    """
    discovered_task_cgroup_paths = {task.cgroup_path for task in discovered_tasks}
    containers_cgroup_paths = {container.cgroup_path for container in known_containers}

    # Filter out containers which are still running according to Mesos agent.
    # In other words pick orphaned containers.
    containers_to_delete = [container for container in known_containers
                            if container.cgroup_path not in discovered_task_cgroup_paths]

    # Filter out tasks which are monitored using "Container abstraction".
    # In other words pick new, not yet monitored tasks.
    new_tasks = [task for task in discovered_tasks
                 if task.cgroup_path not in containers_cgroup_paths]

    return new_tasks, containers_to_delete


@dataclass
class DetectionRunner:
    """Watch over tasks running on this cluster on this node, collect observation
    and report externally (using storage) detected anomalies.
    """
    node: mesos.MesosNode
    storage: storage.Storage
    detector: detectors.AnomalyDetector
    action_delay: float = 0.  # [s]
    rdt_enabled: bool = True
    extra_labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.containers: Dict[MesosTask, Container] = {}

    def wait_or_finish(self):
        """Decides how long one run takes and when to finish.
        TODO: handle graceful shutdown on signal
        """
        time.sleep(self.action_delay)
        return True

    def _sync_containers_state(self, tasks):
        """Sync internal state of runner by removing orphaned containers, and creating containers
        for newly arrived tasks, and synchronizing containers' state.

        Function is responsible for cleaning or initializing measurements stateful subsystems
        and their external resources, e.g.:
        - perf counters opens file descriptors for counters,
        - resctrl (ResGroups) creates and manages directories under resctrl fs and scarce "clsid"
            hardware identifiers

        """
        # Find difference between discovered Mesos tasks and already watched containers.
        new_tasks, containers_to_cleanup = _calculate_desired_state(
            tasks, list(self.containers.values()))

        # Cleanup and remove orphaned containers (cleanup).
        for container_to_cleanup in containers_to_cleanup:
            container_to_cleanup.cleanup()
        self.containers = {task: container
                           for task, container in self.containers.items()
                           if task in tasks}

        # Create new containers and store them.
        for new_task in new_tasks:
            self.containers[new_task] = Container(new_task.cgroup_path,
                                                  rdt_enabled=self.rdt_enabled)

        # Sync state of individual containers.
        for container in self.containers.values():
            container.sync()

    @logger.trace(log)
    def run(self):
        if self.rdt_enabled and not check_resctrl():
            return
        elif not self.rdt_enabled:
            log.warning('Rdt disabled. Skipping collecting measurements '
                        'and resctrl synchronization')
        else:
            # Resctrl is enabled and available - cleanup previous runs.
            cleanup_resctrl()

        if not are_privileges_sufficient():
            log.critical("Impossible to use perf_event_open. You need to: be root; or adjust "
                         "/proc/sys/kernel/perf_event_paranoid; or has CAP_SYS_ADMIN capability"
                         " set. See man 2 perf_event_open for details.")
            return

        while True:
            # Collect information about tasks running on node.
            tasks = self.node.get_tasks()

            # Keep sync of found tasks and internally managed containers.
            self._sync_containers_state(tasks)

            # Platform information
            platform, platform_metrics, platform_labels = platforms.collect_platform_information()

            # Common labels
            common_labels = dict(platform_labels, **self.extra_labels)

            # Update platform_metrics with common labels.
            for metric in platform_metrics:
                metric.labels.update(common_labels)

            # Build labeled tasks_metrics and task_metrics_values.
            tasks_measurements: TasksMeasurements = {}
            tasks_metrics: List[Metric] = []
            for task, container in self.containers.items():
                task_measurements = container.get_measurements()
                tasks_measurements[task.task_id] = task_measurements
                task_metrics = create_metrics(task, task_measurements)
                for task_metric in task_metrics:
                    task_metric.labels.update(common_labels)
                tasks_metrics += task_metrics

            self.storage.store(platform_metrics + tasks_metrics)

            # Wrap tasks with metrics
            anomalies, extra_metrics = self.detector.detect(platform, tasks_measurements)

            anomaly_metrics = convert_anomalies_to_metrics(anomalies)

            # Update anomaly & extra metrics with common labels.
            for metric in anomaly_metrics + extra_metrics:
                metric.labels.update(common_labels)

            self.storage.store(anomaly_metrics + extra_metrics)

            if not self.wait_or_finish():
                break

        # cleanup
        for container in self.containers.values():
            container.cleanup()
