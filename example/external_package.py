from owca.metrics import Metric
from owca.detectors import (TasksMeasurements, ContentionAnomaly,
                            ContendedResource, AnomalyDetector, TasksResources)
from owca.mesos import TaskId
from owca.platforms import Platform


class ExampleDetector(AnomalyDetector):
    """Always return anomaly for given task."""

    def __init__(self, task_id: TaskId):
        self.task_id = task_id

    def detect(self, platform: Platform,
               tasks_measurements: TasksMeasurements,
               tasks_resources: TasksResources,
               ):
        anomalies = [
            ContentionAnomaly(
                contended_task_id=self.task_id,
                contending_task_ids=['some', 'ids'],
                resource=ContendedResource.CPUS,
                metrics=[Metric(name="cpu_threshold", value="90", type="gauge")],
            )
        ]
        debugging_metrics = [
            Metric(
                name='some_debug',
                value=2,
                type="gauge",
                labels=dict(
                    version='2.0',
                )
            )
        ]
        return anomalies, debugging_metrics
