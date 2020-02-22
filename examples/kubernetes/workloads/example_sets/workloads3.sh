kubectl scale sts memcached-mutilate-medium --replicas=1
sleep 5
kubectl scale sts stress-stream-medium --replicas=1
sleep 5
kubectl scale sts sysbench-memory-medium --replicas=1
sleep 5
kubectl scale sts specjbb-preset-medium --replicas=1
sleep 5
kubectl scale sts redis-memtier-big --replicas=1
sleep 5
kubectl scale sts mysql-hammerdb-small --replicas=1
sleep 5
kubectl scale sts sysbench-memory-big --replicas=1
sleep 5
kubectl scale sts memcached-mutilate-big --replicas=1
sleep 5
kubectl scale sts stress-stream-big --replicas=1
sleep 5
kubectl scale sts stress-stream-small --replicas=1
sleep 5
kubectl scale sts sysbench-memory-small --replicas=1
sleep 5
kubectl scale sts memcached-mutilate-small --replicas=1
sleep 5
kubectl scale sts stress-stream-medium --replicas=2
sleep 5
kubectl scale sts sysbench-memory-medium --replicas=2
sleep 5
kubectl scale sts redis-memtier-big --replicas=2
sleep 5
kubectl scale sts mysql-hammerdb-small --replicas=2
sleep 5
kubectl scale sts sysbench-memory-big --replicas=2
sleep 5
kubectl scale sts stress-stream-small --replicas=2
sleep 5
kubectl scale sts sysbench-memory-small --replicas=2
sleep 5
kubectl scale sts stress-stream-medium --replicas=3
sleep 5
kubectl scale sts redis-memtier-big --replicas=3
sleep 5
kubectl scale sts mysql-hammerdb-small --replicas=3
sleep 5
kubectl scale sts sysbench-memory-small --replicas=3
sleep 5
kubectl scale sts stress-stream-medium --replicas=4
sleep 5
kubectl scale sts redis-memtier-big --replicas=4
sleep 5
kubectl scale sts mysql-hammerdb-small --replicas=4
sleep 5
kubectl scale sts sysbench-memory-small --replicas=4
sleep 5
kubectl scale sts stress-stream-medium --replicas=5
sleep 5
kubectl scale sts redis-memtier-big --replicas=5
sleep 5
kubectl scale sts stress-stream-medium --replicas=6
sleep 5
kubectl scale sts redis-memtier-big --replicas=6
sleep 5
kubectl scale sts stress-stream-medium --replicas=7
sleep 5
kubectl scale sts stress-stream-medium --replicas=8
sleep 5
