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
import logging
from collections import defaultdict, Counter

from wca.logger import CountingHandler


def test_counting_handler():
    logger_foo = logging.getLogger("foo")
    logger_foo_bar = logging.getLogger("foo.bar")
    logger_foo.setLevel(10)

    cnt = defaultdict(Counter)
    hdl = CountingHandler(cnt)
    logger_foo.addHandler(hdl)

    logger_foo.warning("baz")
    logger_foo.warning("baz")
    logger_foo.warning("baz")
    logger_foo.error("baz")
    logger_foo.error("baz")
    logger_foo.log(33, "baz")

    logger_foo_bar.error("baz")
    logger_foo_bar.warning("baz")

    assert cnt["foo"][logging.WARNING] == 3
    assert cnt["foo"][logging.ERROR] == 2
    assert cnt["foo"][33] == 1
    assert sum(cnt["foo"].values()) == 6

    assert cnt["foo.bar"][logging.WARNING] == 1
    assert cnt["foo.bar"][logging.ERROR] == 1
    assert sum(cnt["foo.bar"].values()) == 2
