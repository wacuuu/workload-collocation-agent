# Copyright (c) 2019 Intel Corporation
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

from wca.metrics import MetricSource, METRICS_METADATA


METRICS_DOC_PATH = 'docs/metrics.rst'

INTRO = """
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

"""


def generate_docs(source: MetricSource = None):
    metric_table = ""
    metric_table += '==== ==== ==== =====\n'
    metric_table += 'Name Type Unit Help\n'
    metric_table += '==== ==== ==== =====\n'

    for metric in METRICS_METADATA:
        metadata = METRICS_METADATA[metric]
        metric_table += '| {} | {} | {} | {} |\n'.format(
                metric, metadata.type, metadata.unit, metadata.help)

    metric_table += '==== ==== ==== ====='

    return metric_table


if __name__ == '__main__':
    with open(METRICS_DOC_PATH, 'w') as f:
        f.write(INTRO)
        f.write(generate_docs())
