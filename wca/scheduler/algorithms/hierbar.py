import statistics
from collections import Counter, defaultdict
from functools import reduce
from typing import Tuple, List, Dict
import logging

from wca.logger import TRACE
from wca.scheduler.algorithms.least_used_bar import LeastUsedBAR
from wca.scheduler.algorithms.base import used_free_requested, divide_resources, \
    calculate_read_write_ratio, sum_resources
from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType as rt, NodeName

log = logging.getLogger(__name__)

class HierBAR(LeastUsedBAR):

    def __init__(self,
                 data_provider: DataProvider,
                 dimensions=(rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 alias=None,
                 ):
        LeastUsedBAR.__init__(self, data_provider, dimensions, alias=alias)

    def app_fit_nodes(self, node_names, app_name, data_provider_queried
                      ) -> Tuple[List[NodeName], Dict[NodeName, str]]:

        # TODO: optimize this context should be calculated eariler (add passed for every node)
        nodes_capacities, assigned_apps_counts, apps_spec, _ = data_provider_queried

        def resources_to_shape(resources: Dict[rt, float]):
            # for visualization reasons always normalized to 1 cpu
            cpus = resources[rt.CPU]
            return tuple(sorted({r:int(v/cpus) for r,v in resources.items()}.items()))

        # Reverse node_capacities to find type of node
        node_shapes = {node_name: resources_to_shape(node_capacity) for node_name, node_capacity in nodes_capacities.items()}

        shapes_to_nodes = defaultdict(list)
        for node_name, shape in node_shapes.items():
            shapes_to_nodes[shape].append(node_name)
        shapes_to_nodes = dict(shapes_to_nodes)

        # Number of nodes of each class
        # log.log(TRACE, '[Prioritize] Node classes: %r', dict(Counter(node_shapes)))

        requested = apps_spec[app_name]
        # Calculate all classes bar (fitness) score
        class_bar_variances = {}  # class_shape: fit
        for class_shape, node_names_of_this_shape in shapes_to_nodes.items():
            nodes_of_this_shape = [nodes_capacities[node_name] for node_name in node_names_of_this_shape]
            sum_resources_of_nodes = reduce(sum_resources, nodes_of_this_shape)
            averaged_resources_of_class = divide_resources(
                sum_resources_of_nodes,
                {r:len(nodes_of_this_shape) for r in sum_resources_of_nodes.keys()},
            )
            membw_read_write_ratio = calculate_read_write_ratio(averaged_resources_of_class)
            requested_empty_fraction = divide_resources(
                requested,
                averaged_resources_of_class,
                membw_read_write_ratio
            )

            variance = statistics.variance(requested_empty_fraction.values())
            # log.log(TRACE, '[Prioritize] class_shape=%s average_resources_of_class=%s requested=%s requested_fraction=%s variance=%s', class_shape, averaged_resources_of_class, requested, requested_empty_fraction, variance)
            class_bar_variances[class_shape] = variance

        log.log(TRACE, '[Filter][app=%s] app_shape=%s scores for each class of nodes: %s',
                  app_name, resources_to_shape(requested), class_bar_variances)

        # Start with best class (least variance)
        failed = {} # node_name to error string
        for class_shape, class_bar_variance in sorted(class_bar_variances.items(), key=lambda x:x[1]):

            best_node_names_according_shape = shapes_to_nodes[class_shape]

            accepted_node_names = list(set(node_names) & set(best_node_names_according_shape))
            # if we found at least on node is this class then leave
            if accepted_node_names:
                break
            else:
                log.debug('[Filter][app=%s] no enough nodes in best class (shape=%s, nodes=[%s]), take next class',
                          app_name, class_shape, ','.join(best_node_names_according_shape))
        else:
            assert False, 'last class has to match!'

        failed_names = set(node_names) - set(accepted_node_names)
        for failed_node_name in failed_names:
            failed_node_variance = class_bar_variances[node_shapes[failed_node_name]]
            failed[failed_node_name] = 'Not best class (best_variance=%.2f this=%.2f)' % (class_bar_variance,  failed_node_variance)

        log.debug(
            '[Filter][app=%s] nodes=[%s] best_class=%r best_class_variance=%.3f best_nodes=[%s]',
            app_name, ','.join(node_names), dict(class_shape),
            class_bar_variance, ','.join(accepted_node_names))

        return accepted_node_names, failed

