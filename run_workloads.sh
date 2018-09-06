#!/bin/bash -ex

# Run multiple configurations files run like this:
#ls -1 config-*.sh | xargs -n1 -P 8 bash run_workloads.sh 

first_arg=$1
config_file=${first_arg:-config.sh}

echo Using: $config_file

# Shared among all workloads. Variables believed to be often changed.
[ ! -e "$config_file" ] && echo "A file $config_file does not exist." && exit 1
source $config_file

prometheus_port=$prometheus_smallest_port

# kill all job on that cluster/role/environment
aurora job list $cluster/$role/staging$env_uniq_id | xargs --no-run-if-empty -n 1 -P $total_jobs_per_env aurora job killall

# specjbb
export qps=500
export load_generator_port=42000
for i in $(seq 0 $((specjbb_instances_count-1))); do
    export wrapper_prometheus_port=$prometheus_port
    prometheus_port=$((prometheus_port+1))
    export workload_uniq_id=$load_generator_port
    aurora job create $cluster/$role/staging${env_uniq_id}/specjbb_controller--${workload_uniq_id} workloads/SpecJBB/specjbb.aurora
    aurora job create $cluster/$role/staging${env_uniq_id}/specjbb_injector--${workload_uniq_id} workloads/SpecJBB/specjbb.aurora
    aurora job create $cluster/$role/staging${env_uniq_id}/specjbb_backend--${workload_uniq_id} workloads/SpecJBB/specjbb.aurora

    export load_generator_port=$((load_generator_port+1))
done

# ycsb + casandra
# Note: currently works only for root role.
export cassandra_port=9042
export jmx_port=7199
for i in $(seq 0 $((ycsb_cassandra_instances_count-1))); do
    export wrapper_prometheus_port=$prometheus_port
    prometheus_port=$((prometheus_port+1))
    export workload_uniq_id=$cassandra_port
    aurora job create $cluster/$role/staging$env_uniq_id/cassandra--$workload_uniq_id workloads/cassandra_ycsb/cassandra_ycsb.aurora
    sleep 1
    aurora job create $cluster/$role/staging$env_uniq_id/ycsb--$workload_uniq_id workloads/cassandra_ycsb/cassandra_ycsb.aurora

    export cassandra_port=$((cassandra_port+1))
    export jmx_port=$((jmx_port+1))
done

# rpc-perf + twemcache 
export application_listen_port=11211
export application_image='serenity/twemcache'
export application_image_tag=1
export application=twemcache
for i in $(seq 0 $((rpcperf_twemcache_instances_count-1))); do
    export wrapper_prometheus_port=$prometheus_port
    prometheus_port=$((prometheus_port+1))
    export workload_uniq_id=$application_listen_port
    aurora job create $cluster/$role/staging$env_uniq_id/$application--$workload_uniq_id workloads/rpc-perf/rpc-perf.aurora
    aurora job create $cluster/$role/staging$env_uniq_id/rpc-perf--$workload_uniq_id workloads/rpc-perf/rpc-perf.aurora

    export application_listen_port=$((application_listen_port+1))
done

# rpc-perf + redis
export application_listen_port=6789
export application=redis
export application_image='serenity/redis'
export application_image_tag=1
for i in $(seq 0 $((rpcperf_redis_instances_count-1))); do
    export wrapper_prometheus_port=$prometheus_port
    prometheus_port=$((prometheus_port+1))
    export workload_uniq_id=$application_listen_port
    aurora job create $cluster/$role/staging$env_uniq_id/$application--$workload_uniq_id workloads/rpc-perf/rpc-perf.aurora
    aurora job create $cluster/$role/staging$env_uniq_id/rpc-perf--$workload_uniq_id workloads/rpc-perf/rpc-perf.aurora

    export application_listen_port=$((application_listen_port+1))
done

# tensorflow train
for i in $(seq 0 $((tf_train_instances_count-1))); do
    export wrapper_prometheus_port=$prometheus_port
    prometheus_port=$((prometheus_port+1))
    export workload_uniq_id=$i
    aurora job create $cluster/$role/staging$env_uniq_id/tf_train--$workload_uniq_id workloads/tensorflow-train/tensorflow_train.aurora
done

# tensorflow inference
for i in $(seq 0 $((tf_inference_instances_count-1))); do
    export wrapper_prometheus_port=$prometheus_port
    prometheus_port=$((prometheus_port+1))
    export workload_uniq_id=$i
    aurora job create $cluster/$role/staging$env_uniq_id/tf_inference--$workload_uniq_id workloads/tensorflow-inference/tensorflow_inference.aurora
done
