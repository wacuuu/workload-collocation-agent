# Template file.
# Please copy to config.sh and modify values to your needs.

# Variables believed to be often changed among experiments.

export cluster=example
export role=root
export env_uniq_id=16
export application_host_ip=100.64.176.16
export load_generator_host_ip=100.64.176.17
export wrapper_kafka_brokers=100.64.176.12:9092
export docker_registry=100.64.176.12:80

# The lowest prometheus exposition port to be used.
#   Prometheus ports are assigned sequantially
#   incrementing by 1.
prometheus_smallest_port=9091

# Instances count for workloads (workloads pairs).
specjbb_instances_count=2
ycsb_cassandra_instances_count=2
rpcperf_twemcache_instances_count=4
rpcperf_redis_instances_count=4
tf_train_instances_count=2
tf_inference_instances_count=2
