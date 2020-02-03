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


from unittest.mock import patch

from io import StringIO

from wca.metrics import Metric, MetricType
from wrapper.parser_mysql_tpm_gauge import parse


@patch('builtins.print')
def test_parse(mock_print):
    data = """TPM: 59040.000000
        TPM: 53460.000000
        TPM: 55080.000000
        TPM: 60720.000000
    """

    number_of_reads = len(data.splitlines())
    input_ = StringIO(data)

    got = []
    for _ in range(number_of_reads):
        got.extend(parse(input_, '', None, {}, 'hammerdb_'))
    expected = [
        Metric('hammerdb_tpm', value=59040, labels={},
               type=MetricType.GAUGE,
               help="TPM (transaction per minute) from mysql"),
        Metric('hammerdb_tpm', value=53460, labels={},
               type=MetricType.GAUGE,
               help="TPM (transaction per minute) from mysql"),
        Metric('hammerdb_tpm', value=55080, labels={},
               type=MetricType.GAUGE,
               help="TPM (transaction per minute) from mysql"),
        Metric('hammerdb_tpm', value=60720, labels={},
               type=MetricType.GAUGE,
               help="TPM (transaction per minute) from mysql")
    ]

    assert expected == got
