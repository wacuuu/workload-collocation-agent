# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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

# SLO (service level objective) per workload. 
#   Set to "inf" to set SLO to infinity (any number divided by infinity gives 0).
#   Use the same units as for SLI.
export specjbb_slo="inf"
export ycsb_cassandra_slo="inf"
export rpcperf_twemcache_slo="inf"
export rpcperf_redis_slo="inf"
export tf_train_slo="inf"
export tf_inference_slo="inf"

total_jobs_per_env=29

# Total jobs per config is:
# 15 + 4 + 4 + 4 + 2 = 29
