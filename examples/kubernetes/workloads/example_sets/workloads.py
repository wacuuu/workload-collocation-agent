import sys
sleep=int(sys.argv[1])
d = {
'memcached-mutilate-medium': 1,
'stress-stream-medium': 8,
'sysbench-memory-medium': 2,
'specjbb-preset-medium': 1,
'redis-memtier-big': 6,

'mysql-hammerdb-small': 4,
'sysbench-memory-big': 2,
'specjbb-preset-big-60': 0,
'memcached-mutilate-big': 1,
'stress-stream-big': 1,
'specjbb-preset-big-220': 0,
'redis-memtier-small': 0,

'stress-stream-small': 2,
'specjbb-preset-small': 0,
'sysbench-memory-small': 4,
'memcached-mutilate-small': 1,
'redis-memtier-medium': 0,

}


tuples = []

for k, v in d.items():
    ws = []
    for i in range(1, v+1):
        ws.append((k, i))
    tuples.append(ws)

from pprint import pprint

from itertools import zip_longest

for w in zip_longest(*tuples):
    for w1 in w:
        if w1 is not None:
            print('kubectl scale sts %s --replicas=%s'%w1)
            print('sleep %s'%sleep)

#kubectl scale statefulset redis-memtier-small': 0
#kubectl scale statefulset redis-memtier-big': 0
#kubectl scale statefulset redis-memtier-medium': 0
#
