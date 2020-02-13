import pytest

from wca.scheduler.types import ResourceType as rt

# def used_resources_on_node(dimensions, assigned_apps_counts, apps_spec) -> Resources:
# def free_resources_on_node(dimensions: Iterable[rt], capacity: Resources, used: Resources) -> Resources:
# def membw_check(requested: Resources, used: Resources, capacity: Resources) -> bool:


def build_resources(cpu=None, mem=None, membw_read=None, membw_write=None):
    r = {rt.CPU: cpu, rt.MEM: mem, rt.MEMBW_READ: membw_read, rt.MEMBW_WRITE: membw_write}
    r = {resource: val for resource, val in r.items() if val is not None}
    return r

def build_resources_2(membw_read=None, membw_write=None):
    return build_resources(None, None, membw_read, membw_write)


# @pytest.mark.parametrize(
#     'requested, used, capacity, expected', (
#         # no membw_read and membw_write dimensions, should return True,
#         # despite requested larger than free
#         (build_resources(100, 100), build_resources(5, 5), build_resources(10, 10), True),

#         # enough resources
#         (build_resources_2(3, 1), build_resources_2(1, 1), build_resources_2(40, 10), True),

#         # not enough, but just calculating seperately each
#         # dimension (membw_write, membw_read) none is exceeded
#         (build_resources_2(10, 1), build_resources_2(30, 0), build_resources_2(40, 10), False),
#     )
# )
# def test_membw_check(requested, used, capacity, expected):
#     assert expected == membw_check(requested, used, capacity)


def test_sum_resources():
    sum_ = sum_resources(build_resources(3, 3), build_resources(2, 2)) 
    assert sum_[rt.CPU] == 5 and sum_[rt.MEM] == 5


def test_substract_resources():
    sub_ = substract_resources(build_resources(cpu=3, mem=3), build_resources(cpu=2, mem=2)) 
    assert sub_[rt.CPU] == 1 and sub_[rt.MEM] == 1


def test_flat_membw_read_write():
    r = flat_membw_read_write(build_resources(3, 3, 4, 1), 4)
    assert rt.MEMBW_READ not in r and rt.MEMBW_WRITE not in r
    assert r[rt.MEMBW_FLAT] == 8.0
    assert r[rt.CPU] == 3 and r[rt.MEM] == 3

def test_divide_resources():
    a = build_resources(3, 3, 4, 1)
    b = build_resources(2, 2, 8, 2)
    c = divide_resources(a, b)
    assert c[rt.CPU] == 3.0/2.0 and c[rt.MEM] == 3.0/2.0
    assert c[rt.MEMBW_FLAT] == 0.5


def test_used_resources_on_node():
    dimensions = {rt.CPU, rt.MEM}
    assigned_apps_counts = {'node1': {'stress_ng': 8}}
    apps_spec = {'stress_ng': {rt.CPU: 8, rt.MEM: 10}}
    r = used_resources_on_node(dimensions, assigned_apps_counts, apps_spec)
    assert r[rt.CPU] == 64
    assert r[rt.MEM] == 80
