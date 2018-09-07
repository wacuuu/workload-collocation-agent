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

# Docker images tags to be used.
common_tag=<DOCKER_TAG>
export specjbb_image_tag=$common_tag
#--
export ycsb_image_tag=$common_tag
#--
export rpcperf_image_tag=$common_tag
export redis_image_tag=$common_tag
export twemcache_image_tag=$common_tag
#--
export tensorflow_train_image_tag=$common_tag
#--
export tensorflow_inference_image_tag=$common_tag

# Instances count for workloads (workloads pairs).
specjbb_instances_count=2
ycsb_cassandra_instances_count=2
rpcperf_twemcache_instances_count=4
rpcperf_redis_instances_count=4
tf_train_instances_count=2
tf_inference_instances_count=1

total_jobs_per_env=29

# Total jobs per config is:
# 15 + 4 + 4 + 4 + 2 = 29
