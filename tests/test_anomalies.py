import pytest

from owca.detectors import convert_anomalies_to_metrics
from owca.testing import anomaly, anomaly_metric


@pytest.mark.parametrize('anomalies,expected_metrics', (
    ([], []),
    ([anomaly('t1', ['t2'])], anomaly_metric('t1', ['t2'])),
    ([anomaly('t2', ['t1', 't3'])], anomaly_metric('t2', ['t1', 't3'])),
))
def test_convert_anomalies_to_metrics(anomalies, expected_metrics):
    metrics_got = convert_anomalies_to_metrics(anomalies)
    assert metrics_got == expected_metrics
