from unittest.mock import MagicMock, Mock

import pytest

from tests.testing import create_json_fixture_mock
from wca.scheduler.data_providers.cluster_data_provider import (
        ClusterDataProvider, MissingBasicResources, Kubeapi, Prometheus,
        Queries, GatheringWSSwithoutMemoryBandwidth)
from wca.scheduler.types import ResourceType


def get_mocked_cluster_data_provider():
    mocked_kubeapi = MagicMock(spec=Kubeapi)
    mocked_kubeapi.request_kubeapi.side_effect = request_kubeapi_side_effect
    mocked_kubeapi.monitored_namespaces = ['default']

    mocked_prometheus = Mock(spec=Prometheus)
    mocked_prometheus.do_query.side_effect = do_query_side_effect
    mocked_prometheus.queries = Queries

    cluster_dp = ClusterDataProvider(kubeapi=mocked_kubeapi, prometheus=mocked_prometheus)

    return cluster_dp


def request_kubeapi_side_effect(*args, **kwargs):
    if args[0] == '/api/v1/nodes':
        return create_json_fixture_mock('kubeapi_nodes').json()
    elif args[0] == '/api/v1/namespaces/default/pods':
        return create_json_fixture_mock('kubeapi_default_ns_pods').json()


def do_query_side_effect(*args, **kwargs):
    if args[0] == Prometheus.queries.NODES_PMM_MEMORY_MODE:
        return create_json_fixture_mock('prometheus_nodes_pmm_memory_mode').json()['data']['result']
    elif args[0] == Prometheus.queries.MEMBW_CAPACITY_READ:
        return create_json_fixture_mock('prometheus_membw_capacity_read').json()['data']['result']
    elif args[0] == Prometheus.queries.MEMBW_CAPACITY_WRITE:
        return create_json_fixture_mock('prometheus_membw_capacity_write').json()['data']['result']
    elif args[0] == Prometheus.queries.NODE_CAPACITY_MEM_WSS:
        return create_json_fixture_mock('prometheus_node_capacity_mem_wss').json()['data']['result']
    elif args[0] == Prometheus.queries.NODE_CAPACITY_DRAM_MEMBW:
        return create_json_fixture_mock(
                'prometheus_node_capacity_dram_membw').json()['data']['result']


@pytest.mark.parametrize('resources', [
    [],
    [ResourceType.CPU],
    [ResourceType.MEM],
    [ResourceType.MEMBW_READ, ResourceType.MEMBW_WRITE]])
def test_get_nodes_capacities_raise_exception_no_cpu_or_mem(resources):
    cluster_dp = get_mocked_cluster_data_provider()

    with pytest.raises(MissingBasicResources):
        cluster_dp.get_nodes_capacities(resources)


@pytest.mark.parametrize('resources', [
    [ResourceType.CPU, ResourceType.MEM, ResourceType.WSS],
    [ResourceType.CPU, ResourceType.MEM, ResourceType.WSS, ResourceType.MEMBW_READ],
    [ResourceType.CPU, ResourceType.MEM, ResourceType.WSS, ResourceType.MEMBW_WRITE],
    ])
def test_get_nodes_capacities_raise_exception_wss_without_mb(resources):
    cluster_dp = get_mocked_cluster_data_provider()

    with pytest.raises(GatheringWSSwithoutMemoryBandwidth):
        cluster_dp.get_nodes_capacities(resources)


CLUSTER_CPU_MEM_CAPACITIES = {
        'node200': {'cpu': 48.0, 'mem': 201},
        'node201': {'cpu': 48.0, 'mem': 201},
        'node202': {'cpu': 48.0, 'mem': 201},
        'node203': {'cpu': 48.0, 'mem': 201},
        'node36': {'cpu': 72.0, 'mem': 404},  # k8s master node
        'node37': {'cpu': 40.0, 'mem': 1064},
        'node38': {'cpu': 40.0, 'mem': 404},
        'node39': {'cpu': 40.0, 'mem': 404},
        'node40': {'cpu': 40.0, 'mem': 1065}
}

CLUSTER_MEMBW_CAPACITIES = {
        'node200': {'membw_read': 255999960000, 'membw_write': 255999960000},
        'node201': {'membw_read': 255999960000, 'membw_write': 255999960000},
        'node202': {'membw_read': 255999960000, 'membw_write': 255999960000},
        'node203': {'membw_read': 255999960000, 'membw_write': 255999960000},
        'node37': {'membw_read': 54400000000, 'membw_write': 14800000000},
        'node38': {'membw_read': 255999960000, 'membw_write': 255999960000},
        'node39': {'membw_read': 255999960000, 'membw_write': 255999960000},
        'node40': {'membw_read': 33200000000, 'membw_write': 12000000000}
}

CLUSTER_CAPACITIES = {}

for node in CLUSTER_CPU_MEM_CAPACITIES:
    if node in CLUSTER_MEMBW_CAPACITIES:
        CLUSTER_CAPACITIES[node] = {
                **CLUSTER_CPU_MEM_CAPACITIES[node],
                **CLUSTER_MEMBW_CAPACITIES[node]}
    else:
        CLUSTER_CAPACITIES[node] = CLUSTER_CPU_MEM_CAPACITIES[node]


@pytest.mark.parametrize('resources, nodes_capacities', [
    ([ResourceType.CPU, ResourceType.MEM], CLUSTER_CPU_MEM_CAPACITIES),
    ([ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW_READ,
        ResourceType.MEMBW_WRITE], CLUSTER_CAPACITIES),
    ])
def test_get_nodes_capacities(resources, nodes_capacities):
    cluster_dp = get_mocked_cluster_data_provider()
    assert nodes_capacities == cluster_dp.get_nodes_capacities(resources)


CLUSTER_APP_COUNT = (
        {'node200': {'memcached-mutilate-big-wss': 1},
         'node201': {'memcached-mutilate-big-wss': 1},
         'node202': {'memcached-mutilate-big-wss': 1},
         'node203': {'memcached-mutilate-big-wss': 1},
         'node36': {},
         'node37': {},
         'node38': {},
         'node39': {'memcached-mutilate-big-wss': 1},
         'node40': {'memcached-mutilate-big-wss': 1}},
        {'memcached-mutilate-big-wss': 2})


@pytest.mark.parametrize('apps_count', [
    (CLUSTER_APP_COUNT),
    ])
def test_get_apps_counts(apps_count):
    cluster_dp = get_mocked_cluster_data_provider()
    assert apps_count == cluster_dp.get_apps_counts()
