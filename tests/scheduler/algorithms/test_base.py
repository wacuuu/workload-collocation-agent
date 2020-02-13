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


# @pytest.mark.parametrize(
#     'capacity, used, expected', (
#         (build_resources(5,5), build_resources(10,10), True),

#         (build_resources_2(1,1), build_resources_2(40,10), True),

#         (build_resources_2(30,0), build_resources_2(40,10), False),
#     )
# )
# def test_free_resources_on_node(capacity, used, expected):
#     assert expected == free_resources_on_node(capacity, used)
