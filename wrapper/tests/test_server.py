import pytest

from owca.metrics import Metric
from wrapper.server import create_message


# These use cases check only simple logic in create_message, as prometheus formatting is checked
# in owca unit tests
@pytest.mark.parametrize("input,expected", [
    ([Metric('counter', 1.0), Metric('counter2', 2.0)],
     200),
    ([Metric('counter    ', 2.0)],
     500),
    ([],
     204)
])
def test_create_message(input, expected):
    response_code, body = create_message(input)
    assert response_code == expected
