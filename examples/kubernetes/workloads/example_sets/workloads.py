import sys, random, pprint
sleep=5

d = {
'memcached-mutilate-big': 4,
'memcached-mutilate-medium': 4,
'memcached-mutilate-small': 4,
'mysql-hammerdb-small': 4,
'redis-memtier-big': 4,
'redis-memtier-medium': 4,
'redis-memtier-small': 4,
'specjbb-preset-big-220': 2,
'specjbb-preset-big-60': 4,
'specjbb-preset-medium': 4,
'specjbb-preset-small': 4,
'stress-stream-big': 4,
'stress-stream-medium': 4,
'stress-stream-small': 4,
'sysbench-memory-big': 4,
'sysbench-memory-medium': 4,
'sysbench-memory-small': 4,
}

x=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 4,  6, 7 ,8, ]


dr = [(k,random.sample(x, 1)[0]) for k in d.keys()]
random.shuffle(dr)



d = dict(dr)


for k, v in d.items():
    print('#   "%s":%d'%(k,v))

print('# total %s' % sum(d.values()))

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

