from typing import Dict, Set, List

from wca.scheduler.cluster_simulator import Node, Resources
from wca.scheduler.types import ResourceType as rt


def prepare_nodes(
        node_specs: Dict[str, Dict],  # node_type to resource dict,
        type_counts: Dict[str, int],  # node_type to number of nodes,
        dimensions: Set[rt]
        ) -> List[Node]:
    """Create cluster with node_specs with number of each kind (node_spec are sorted by name).
    A: {ram: 1}, B: {ram: 10}
    {A: 2, B: 3} result in
    A1, A2, B1, B2, B3 machines
    """

    # Filter only dimensions required.
    node_specs = {node_type: {dim: val for dim, val in node_spec.items() if dim in dimensions}
                  for node_type, node_spec in node_specs.items()}

    nodes = []
    for node_type in sorted(node_specs.keys()):
        for node_id in range(type_counts[node_type]):
            node_name = node_type+'_'+str(node_id)
            node = Node(node_name, available_resources=Resources(node_specs[node_type]))
            nodes.append(node)
    return nodes


#Superseded by prepare_nodes above


def prepare_NxMxK_nodes__demo_configuration(
        apache_pass_count, dram_only_v1_count,
        dram_only_v2_count,
        dimensions={rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE}) -> List[Node]:
    """Taken from WCA team real cluster."""
    print('deprecated! please use prepare_nodes!')
    apache_pass = {rt.CPU: 40, rt.MEM: 1000, rt.MEMBW: 40, rt.MEMBW_READ: 40,
                   rt.MEMBW_WRITE: 10, rt.WSS: 256}
    dram_only_v1 = {rt.CPU: 48, rt.MEM: 192, rt.MEMBW: 200, rt.MEMBW_READ: 150,
                    rt.MEMBW_WRITE: 150, rt.WSS: 192}
    dram_only_v2 = {rt.CPU: 40, rt.MEM: 394, rt.MEMBW: 200, rt.MEMBW_READ: 200,
                    rt.MEMBW_WRITE: 200, rt.WSS: 394}
    nodes_spec = [apache_pass, dram_only_v1, dram_only_v2]

    # Filter only dimensions required.
    for i, node_spec in enumerate(nodes_spec):
        nodes_spec[i] = {dim: val for dim, val in node_spec.items() if dim in dimensions}

    inode = 0
    nodes = []
    for i_node_type, node_type_count in enumerate((apache_pass_count, dram_only_v1_count,
                                                   dram_only_v2_count,)):
        for i in range(node_type_count):
            node = Node(str(inode), available_resources=Resources(nodes_spec[i_node_type]))
            nodes.append(node)
            inode += 1
    return nodes