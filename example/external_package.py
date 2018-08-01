from rmi import detectors
from rmi import mesos
from rmi import metrics


class ExampleDetector(detectors.AnomalyDectector):
    """Always return anomaly for given task."""

    def __init__(self, task_id: mesos.TaskId):
        self.task_id = task_id

    def detect(self, platform, task_measurements):
        anomalies = [
            detectors.Anomaly(
                task_ids=[self.task_id], 
                resource=detectors.ContendedResource.CPUS
            )
        ]
        debugging_metrics = [
            metrics.Metric(
                name='some_debug',
                value=2,
                labels=dict(
                    version='2.0',
                )
            )
        ]
        return anomalies, debugging_metrics
