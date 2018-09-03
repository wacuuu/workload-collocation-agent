from owca.metrics import Metric
from owca.detectors import TasksMeasurements, ContentionAnomaly, ContendedResource, AnomalyDetector
from owca.mesos import TaskId
from owca.platforms import Platform


class ExampleDetector(AnomalyDetector):
    """Always return anomaly for given task."""

    def __init__(self, task_id: TaskId):
        self.task_id = task_id

    def detect(self, platform: Platform, tasks_measurements: TasksMeasurements):
        anomalies = [
            ContentionAnomaly(
                task_ids=[self.task_id],
                resource=ContendedResource.CPUS
            )
        ]
        debugging_metrics = [
            Metric(
                name='some_debug',
                value=2,
                labels=dict(
                    version='2.0',
                )
            )
        ]
        return anomalies, debugging_metrics
