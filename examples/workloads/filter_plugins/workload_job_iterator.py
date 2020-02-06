# Copyright (c) 2020 Intel Corporation
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


def workload_job_iterator(workloads_versions, job_id):
    """
    Build list of dicts, where each dict item has 3 key-value pairs,
    used in the playbook to iterate through 1) workload instances count, 2) workload versions,
    3) job replica count.

    I suppose it does not really match what a jinja2 filter should
    consitute (general purpose, not matching just one use case).
    However, in that particular situation it is much simpler to write the custom filter
    than construct the result using build-in jinja2 filters.

    [(workload_instance_index, workload_version_name, job_replica_index), ... ]
    [ {0, small, 0}, {0, small, 1}, {0, small, 2},
      {1, small, 0}, {1, small, 1}, {1, small, 2},
      {2, big, 0}, {2, big, 1},
      {3, big, 0}, {3, big, 1} ]
    """
    r = []
    for workload_version_name, workload_version in workloads_versions.items():

        try:
            job_replica_count = int(workload_version[job_id]['count'])
        except Exception:
            job_replica_count = 1
        if 'count' not in workload_version:
            job_replica_count = 1

        for workload_instance_index in range(workload_version['count']):
            for job_replica_index in range(job_replica_count):
                r.append({'workload_instance_index': workload_instance_index,
                          'workload_version_name': workload_version_name,
                          'job_replica_index': job_replica_index})
    return r


class FilterModule(object):
    def filters(self):
        return {'workload_job_iterator': workload_job_iterator}
