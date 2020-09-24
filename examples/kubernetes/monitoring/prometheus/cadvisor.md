# Workload scoring for pmem with cadvisor

- [Workload scoring for pmem with cadvisor](#workload-scoring-for-pmem-with-cadvisor)
  - [Why](#why)
  - [How](#how)
    - [Algorithm](#algorithm)
    - [Prerequisites](#prerequisites)
      - [Deployed workloads](#deployed-workloads)
      - [Workload identification](#workload-identification)
      - [Behavior measurement](#behavior-measurement)
      - [Requirement measurement](#requirement-measurement)
    - [Implementation](#implementation)
      - [Infra descritpion](#infra-descritpion)
        - [Workloads](#workloads)
        - [Monitoring](#monitoring)
          - [kube-state-metrics](#kube-state-metrics)
        - [cadvisor](#cadvisor)
      - [Rules](#rules)

This document provides an overlook on how to benchmark an application to asses its possible performance gains using Intel® Optane™ DC Persistent memory. Althoguh the implementation is based on Prometheus rules deployed as operator, concepts and algorithm should be translateable to other systems.

## Why

As good as Workload Collocation Agent is, it is a PoC project with small maintainer group and community. For production grade environmnents something more stable and proven is required, therefore a decision has been made to switch to [cAdvisor](https://github.com/google/cadvisor). Because the way the metrics are gathered and reported differs between the two, it was impossible to take score calculation based on WCA metrics and make it work 1:1 on cAdvisor metrics. Therefore rules has been rewritten to align with new data source.

## How

The description provided is based on prometheus, but the algorithm and part of requirements apply to any system.

### Algorithm

As mentioned in the beginnig the overall goal of the process is to determine if a workload is fit for 2lm node with Intel memory. In general, it answears the question:

*Which will be saturated first on a node with Intel memory dice: memory or any other resource?*

The answear takes form of ratio how many times faster will the other resource(cpu, memory bandwith or working set size) saturated than the memory, for example if score is 1.25 it means that one of the resources will saturate 1.25 times faster than memory. Therefore score interpretation is the following:

| Score | Interpretation|
| -----| --------------|
|0 | workload only allocates memory but doesn't use it or any cpu (perfect candidate) |
| <1| node filled with such workloads, memory will be 100% utilized when constrained by other resource|
| <3 | not perfect but still worth considering as good candidate for 2LM node|
|>>3 | memory utilization will be low because of saturation on other resources|

As mentioned, algorithm looks at 4 different parameters:

- CPU requirements
- Memory requirements
- Memory bandwidth
- Working set size

Score computation depends on couple of parameters describing applications access to memory:

1. *How much memory does it require?* (the more the better)
2. *How much of this memory is actually used most of the time(what is the WSS(working set size))?* (the smaller the better)
3. *What bandwith can we guarantee for an app in communication between CPU cache and memory?* (the bigger the better)
4. *How often does the app reach to memory outside the CPU cache?*

*NOTE*: In the case of algorithm, the scope of data is the whole application, as it will be seen in implementation, all pods matched to certain app deployed in statefull sets.

Based on the data gathered answearing those questions, algorithm works as follows:

1. Prepare an entry that mocks existance of a PMEM node with some assumed parameters, as it will be required for comparasion
2. Measure application instances behavior
3. Aggregate data to represent overall application behavior
4. Asses the most problematic limitation that will be returned as the score

The whole point of the implemetation provided as example later on is to prepare all the data required by 5 operations: 3 to get ratio of requirements of cpu, bandwith and wss in relation to memory, then normalising it based on the mock pmem node and returnig the max(so the worst possible) score.

### Prerequisites

List of concepts required to know before implementation explaination

#### Deployed workloads

The algorithm asumes that it is used in production or production like environment. It is supposed to be deployed alongside the service.

#### Workload identification

The algorithm requires that there will be a way to identify all instances of a workload. That is there has to be for example a common label on all pods identifying the workload they belong to(see how "app" label is handled in example).

#### Behavior measurement

Shift to cAdvisor has been made, however if one requires, they can use a different software. I has to be able to report memory bandwith based on resctrl, perf events, specifically offcore_requests.demand_data_rd and offcore_requests.demand_rfo, as well as working set size based on /proc/smaps file. Fortunately cAdvisor can do this all.

*WARNING*: as of today some changes required for full readines are still awaiting to be merged. For now, [this fork and branch](https://github.com/wacuuu/cadvisor/tree/jwalecki/even-more-magic) contains all needed features.

#### Requirement measurement

Besides measuring application behavior, one must take the requirements into consideration, namely requirement for CPU and memory. This can be easly done by using kube-state-metrics. If this is not possible, one can manually apply the requirements, although it would require to put them for every benchamrked application.

### Implementation

The following part describes how is the example in this repo implemented.

#### Infra descritpion

Example consists of example workloads and monitoring setup.

##### Workloads

Example workloads are in [this directory](../../workloads). Those are just reference applications used to test the solution. Only thing important for further explanationa is the app label. It is used to identify the workload in rules.

##### Monitoring

Deployment consist of 3 independent parts: cadvisor, prometheus and kube-state-metrics.

###### kube-state-metrics

Nothing particulary important in this part of deployment. All the details are[here](../kube-state-metrics). It is set up in such a way that it is accesible for prometheus deployed as operator.

##### cadvisor

Deployment as daemonset is defined



#### Rules
