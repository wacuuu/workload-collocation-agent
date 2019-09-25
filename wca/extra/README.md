# WIP NUMA Allocator docs


## Assumptions

- Centos 7.6 (pytnon 3.6 available) or installed from epel-release
- running using sources (no pex file)
- running without real orchestrator (no Kubernetes nor Mesos)
- tasks will be run manually using cgexec from libcgroup-tools package


## Preparation

### 1. Installation 

Use `ppalucki` fork for PoC 

```
# Get sources ...
git clone https://github.com/ppalucki/owca/ wca
cd wca
git checkout ppalucki/numa

# set proper ACLs for config file
chmod og-rw configs/extra/numa_allocator.yaml

# Install runtime, tools and stress-ng as workload ...
sudo yum install -y epel-release
sudo yum install -y python3.6 stress-ng libcgroup-tools
sudo python36 -mensurepip
sudo python36 -mpip install --user pipenv 

pipenv install --dev

PYTHONPATH=. pipenv run python wca/main.py --version
# Should output: unknown_version
```

### 2. Prepare cgroups for tasks: task1, task2


```shell
sudo mkdir /sys/fs/cgroup/{cpu,cpuset,perf_event,cpuset,memory}/{task1,task2}

# cpuset groups requires additional configuration
sudo sh -c "echo 0 > /sys/fs/cgroup/cpuset/task1/cpuset.cpus"
sudo sh -c "echo 0 > /sys/fs/cgroup/cpuset/task1/cpuset.mems"
sudo sh -c "echo 0 > /sys/fs/cgroup/cpuset/task2/cpuset.cpus"
sudo sh -c "echo 0 > /sys/fs/cgroup/cpuset/task2/cpuset.mems"

```

### 3. Run some tasks inside those cgroups


```shell
sudo cgexec -g cpu:task1 -g perf_event:task1 -g cpuset:task1 -g memory:task1 stress-ng -c 1 &
sudo cgexec -g cpu:task2 -g perf_event:task2 -g cpuset:task2 -g memory:task2 stress-ng -c 1 &
```


### 4. Run WCA 

```shell
sudo env PYTHONPATH=. `pipenv --py` wca/main.py  --root --config $PWD/configs/extra/numa_allocator.yaml -l info -l numa_allocator:debug
```

### 5. Observe output (metrics, allocations)

```shell
watch -n1 head /sys/fs/cgroup/cpuset/{task1,task2}/cpuset.{mems,cpus}
```

