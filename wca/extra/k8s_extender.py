import logging
import socketserver

import threading

from wca.detectors import AnomalyDetector, TasksMeasurements, TasksResources, TasksLabels
from wca.platforms import Platform
from pprint import pprint
import http.server
import json
from dataclasses import dataclass, asdict
from typing import Dict, List
log = logging.getLogger(__name__)


@dataclass
class ExtenderArgs:
    Pod: Dict
    Nodes: List
    NodeNames: List

# ExtenderFilterResult represents the results of a filter call to an extender
@dataclass
class ExtenderFilterResult:
    # Filtered set of nodes where the pod can be scheduled; to be populated
    # only if ExtenderConfig.NodeCacheCapable == false
    Nodes: List#: *v1.NodeList
    # Filtered set of nodes where the pod can be scheduled; to be populated
    # only if ExtenderConfig.NodeCacheCapable == true
    NodeNames: List #: *[]string
    # Filtered out nodes where the pod can't be scheduled and the failure messages
    FailedNodes: Dict#: FailedNodesMap
    # Error message indicating failure
    Error: str


@dataclass
class ExtenderBindingArgs:
    # PodName is the name of the pod being bound
    PodName: str
    # PodNamespace is the namespace of the pod being bound
    PodNamespace: str
    # PodUID is the UID of the pod being bound
    PodUID: int
    # Node selected by the scheduler
    Node: str




class K8SHandler(http.server.BaseHTTPRequestHandler):

    vars = 5

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        self.log_request()
        try:
            post_json = json.loads(self.rfile.read(content_length).decode())
            pprint(post_json)
        except Exception:
            log.warning('cannot parse rfile!')
            post_json = None

        if self.path == "/api/scheduler/filter":
            result = self._filter(args=post_json)
        # elif self.path == "/api/scheduler/prioritize":
        #     result = self._prioritize(args=post_json)
        # elif self.path == "/api/scheduler/bind":
        #     result = self._bind(args=post_json)
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(self.serialize(result))

    def _filter(self, args: ExtenderArgs) -> ExtenderFilterResult:
        return None

    # def _prioritize(self, args: ExtenderArgs) -> HostPriorityList:
    #     pass

    # def _bind(self, args: ExtenderBindingArgs) -> ExtenderBindingResult:
    #     pass

    def serialize(self, obj):
        # return json.dumps(asdict(obj)).encode()
        return json.dumps(K8SHandler.vars).encode()


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def start_server(port):
    with http.server.HTTPServer(('', port), K8SHandler) as httpd:
        log.info('serving at port: %s', port)
        httpd.serve_forever()

@dataclass
class K8SExtenderDetector(AnomalyDetector):

    """Cyclic deterministic dummy anomaly detector."""
    port = 12345

    def __post_init__(self):
        threading.Thread(target=start_server, args=(self.port,), daemon=True).start()

    def detect(self,
               platform: Platform,
               tasks_measurements: TasksMeasurements,
               tasks_resources: TasksResources,
               tasks_labels: TasksLabels
               ):
        K8SHandler.vars = len(tasks_labels)
        log.debug('vars=%s', K8SHandler.vars)
        return [], []



