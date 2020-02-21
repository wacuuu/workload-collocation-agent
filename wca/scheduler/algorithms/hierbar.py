import statistics
from collections import Counter
from typing import Tuple, List, Dict
import logging

from wca.scheduler.algorithms.bar import BAR
from wca.scheduler.algorithms.base import used_free_requested, divide_resources, \
    calculate_read_write_ratio
from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.types import ResourceType as rt, NodeName

log = logging.getLogger(__name__)

class HierBAR(BAR):

    def __init__(self,
                 data_provider,
                 dimensions=(rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 alias=None,
                 ):
        BAR.__init__(self, data_provider, dimensions, alias=alias)

    def app_fit_nodes(self, node_names, app_name, data_provider_queried
                      ) -> Tuple[List[NodeName], Dict[NodeName, str]]:

        # TODO: optimize this context should be calculated eariler (add passed for every node)
        nodes_capacities, assigned_apps_counts, apps_spec, _ = data_provider_queried

        def resources_to_shape(resources: Dict[rt, float]):
            return tuple(sorted(resources.items()))

        # Reverse node_capacities to find type of node
        node_shapes = [resources_to_shape(node_capacity) for node_capacity in nodes_capacities.values()]
        # Number of nodes of each class
        nodes_classes = Counter(node_shapes)
        requested = apps_spec[app_name]

        # Calculate all classes bar (fitness) score
        class_bar_scores = {}  # class_shape: fit
        for class_shape, number_of_nodes in nodes_classes.items():
            class_capacity = dict(class_shape) # reverse from shape->resources
            membw_read_write_ratio = calculate_read_write_ratio(class_capacity)
            requested_empty_fraction = divide_resources(
                requested, class_capacity,
                membw_read_write_ratio
            )
            variance = statistics.variance(requested_empty_fraction.values())
            class_bar_scores[class_shape] = variance

        log.debug('task %s (shape=%s) scores for each class of nodes: %s',
                  app_name, requested, class_bar_scores)

        # Start with best class (least variance)
        accepted_node_names = []
        failed = {} # node_name to error string
        for class_shape, class_bar_score in sorted(class_bar_scores.items(), key=lambda x:x[1]):

            # Check one class
            # Find node from this class
            for node_name in node_names:
                node_capacity = nodes_capacities[node_name]
                node_shape = resources_to_shape(node_capacity)
                node_score = class_bar_scores[node_shape]
                if node_shape == class_shape:
                    accepted_node_names.append(node_name)
                elif not node_name in failed:
                    # From worse class
                    failed[node_name] = 'Not best shape (has=%s best=%s)' % (node_score, class_bar_score)

            # if we found at least on node is this class then leave
            if accepted_node_names:
                break
        else:
            assert False, 'last class has to match!'

        return accepted_node_names, failed

